"""
Graph RAG implementation for Text2SQL application.

This module builds and maintains knowledge graphs for:
1. Database schema relationships
2. Query patterns and their relationships
3. Entity relationships from queries
"""

import json
import hashlib
import sqlite3
from typing import Dict, List, Optional, Tuple, Any
import networkx as nx
from datetime import datetime
from langchain_community.utilities import SQLDatabase
try:
    from constants import DATABASE
except ImportError:
    from src.constants import DATABASE


class SchemaGraphBuilder:
    """Builds a knowledge graph from database schema."""
    
    def __init__(self, db: SQLDatabase):
        self.db = db
        self.graph = nx.DiGraph()
        self._build_schema_graph()
    
    def _build_schema_graph(self):
        """Build graph from database schema."""
        # Get all tables
        tables = self.db.get_usable_table_names()
        
        # Add table nodes
        for table in tables:
            self.graph.add_node(f"table:{table}", type="table", name=table)
            
            # Get table schema
            try:
                schema = self.db.get_table_info_no_throw([table])
                columns = self._parse_schema(schema)
                
                # Add column nodes and relationships
                for col_name, col_type in columns:
                    col_node = f"column:{table}.{col_name}"
                    self.graph.add_node(col_node, type="column", name=col_name, 
                                      data_type=col_type, table=table)
                    self.graph.add_edge(f"table:{table}", col_node, 
                                       relationship="has_column")
                
                # Detect foreign key relationships
                self._detect_foreign_keys(table, columns)
                
            except Exception as e:
                print(f"Error processing table {table}: {e}")
    
    def _parse_schema(self, schema: str) -> List[Tuple[str, str]]:
        """Parse schema string to extract columns."""
        columns = []
        for line in schema.split('\n'):
            if 'CREATE TABLE' in line.upper() or not line.strip():
                continue
            # Parse column definition (simplified)
            parts = line.strip().split()
            if len(parts) >= 2:
                col_name = parts[0].strip('`"[]')
                col_type = parts[1].upper()
                columns.append((col_name, col_type))
        return columns
    
    def _detect_foreign_keys(self, table: str, columns: List[Tuple[str, str]]):
        """Detect foreign key relationships."""
        # Common foreign key patterns
        for col_name, col_type in columns:
            # Pattern: table_id or tableId
            if col_name.endswith('_id') or 'Id' in col_name:
                # Try to find referenced table
                ref_table = col_name.replace('_id', '').replace('Id', '').lower()
                if ref_table in [n.replace('table:', '') for n in self.graph.nodes() 
                                if n.startswith('table:')]:
                    self.graph.add_edge(
                        f"table:{table}",
                        f"table:{ref_table}",
                        relationship="references",
                        via_column=col_name
                    )
    
    def get_related_tables(self, table: str, max_hops: int = 2) -> List[str]:
        """Get tables related to a given table within max_hops."""
        table_node = f"table:{table}"
        if table_node not in self.graph:
            return []
        
        related = []
        for node in nx.single_source_shortest_path_length(
            self.graph, table_node, cutoff=max_hops
        ).keys():
            if node.startswith('table:') and node != table_node:
                related.append(node.replace('table:', ''))
        
        return related
    
    def get_join_path(self, table1: str, table2: str) -> Optional[List[str]]:
        """Find the shortest path between two tables."""
        try:
            path = nx.shortest_path(
                self.graph,
                f"table:{table1}",
                f"table:{table2}"
            )
            return [n.replace('table:', '') for n in path if n.startswith('table:')]
        except nx.NetworkXNoPath:
            return None
    
    def get_schema_context(self, tables: List[str]) -> str:
        """Get schema context for given tables."""
        context = []
        for table in tables:
            if f"table:{table}" in self.graph:
                # Get table info
                context.append(f"Table: {table}")
                # Get columns
                columns = [n for n in self.graph.neighbors(f"table:{table}") 
                          if n.startswith('column:')]
                for col_node in columns:
                    col_data = self.graph.nodes[col_node]
                    context.append(f"  - {col_data['name']} ({col_data.get('data_type', 'unknown')})")
                
                # Get relationships
                relationships = [e for e in self.graph.edges(f"table:{table}", data=True)
                               if e[1].startswith('table:')]
                for rel in relationships:
                    target_table = rel[1].replace('table:', '')
                    via = rel[2].get('via_column', '')
                    context.append(f"  - References {target_table} via {via}")
        
        return "\n".join(context)


class QueryGraphBuilder:
    """Builds a knowledge graph from queries and their patterns."""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.query_cache = {}
    
    def add_query(self, query_text: str, sql_query: str, result: Any, 
                  entities: List[str] = None, tables: List[str] = None):
        """Add a query to the graph."""
        query_hash = self._hash_query(query_text)
        query_node = f"query:{query_hash}"
        
        # Add query node
        self.graph.add_node(query_node, 
                           type="query",
                           text=query_text,
                           sql=sql_query,
                           timestamp=datetime.now().isoformat())
        
        # Add SQL node
        sql_hash = self._hash_sql(sql_query)
        sql_node = f"sql:{sql_hash}"
        self.graph.add_node(sql_node, type="sql", query=sql_query)
        self.graph.add_edge(query_node, sql_node, relationship="generates")
        
        # Add result node
        result_node = f"result:{query_hash}"
        self.graph.add_node(result_node, type="result", data=str(result))
        self.graph.add_edge(sql_node, result_node, relationship="returns")
        
        # Add entity nodes
        if entities:
            for entity in entities:
                entity_node = f"entity:{entity}"
                self.graph.add_node(entity_node, type="entity", name=entity)
                self.graph.add_edge(query_node, entity_node, relationship="mentions")
        
        # Add table nodes
        if tables:
            for table in tables:
                table_node = f"table:{table}"
                self.graph.add_node(table_node, type="table", name=table)
                self.graph.add_edge(query_node, table_node, relationship="queries")
        
        # Connect to similar queries
        self._connect_similar_queries(query_node, query_text)
        
        return query_hash
    
    def _hash_query(self, query: str) -> str:
        """Create hash for query."""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:8]
    
    def _hash_sql(self, sql: str) -> str:
        """Create hash for SQL query."""
        normalized = ' '.join(sql.upper().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:8]
    
    def _connect_similar_queries(self, new_query_node: str, query_text: str):
        """Connect query to similar queries in the graph."""
        # Simple similarity: check for common entities/tables
        new_entities = set(self._extract_entities(query_text))
        
        for node in self.graph.nodes():
            if node.startswith('query:') and node != new_query_node:
                node_data = self.graph.nodes[node]
                existing_entities = set(self._extract_entities(node_data.get('text', '')))
                
                # If they share entities, connect them
                common = new_entities & existing_entities
                if common:
                    similarity = len(common) / max(len(new_entities), len(existing_entities), 1)
                    if similarity > 0.3:  # 30% similarity threshold
                        self.graph.add_edge(new_query_node, node, 
                                           relationship="similar_to", 
                                           similarity=similarity)
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text (simplified)."""
        # Common entity keywords
        entities = []
        keywords = ['user', 'order', 'product', 'revenue', 'sales', 'customer', 
                   'category', 'brand', 'state', 'city', 'month', 'year']
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                entities.append(keyword)
        return entities
    
    def find_similar_queries(self, query_text: str, top_k: int = 3) -> List[Dict]:
        """Find similar queries in the graph."""
        query_hash = self._hash_query(query_text)
        query_node = f"query:{query_hash}"
        
        if query_node not in self.graph:
            return []
        
        # Get similar queries
        similar = []
        for neighbor in self.graph.neighbors(query_node):
            if neighbor.startswith('query:'):
                edge_data = self.graph[query_node][neighbor]
                similar.append({
                    'query': self.graph.nodes[neighbor]['text'],
                    'sql': self.graph.nodes[neighbor].get('sql', ''),
                    'similarity': edge_data.get('similarity', 0)
                })
        
        # Sort by similarity
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar[:top_k]
    
    def get_query_context(self, query_text: str) -> str:
        """Get context for a query from the graph."""
        similar = self.find_similar_queries(query_text)
        if not similar:
            return ""
        
        context = "Similar queries found:\n"
        for i, sim in enumerate(similar, 1):
            context += f"{i}. Query: {sim['query']}\n"
            context += f"   SQL: {sim['sql']}\n"
            context += f"   Similarity: {sim['similarity']:.2f}\n\n"
        
        return context


class GraphRAG:
    """Main Graph RAG class that combines schema and query graphs."""
    
    def __init__(self, db: SQLDatabase):
        self.schema_graph = SchemaGraphBuilder(db)
        self.query_graph = QueryGraphBuilder()
        self.db = db
    
    def get_context_for_query(self, query_text: str, 
                             extract_tables: bool = True) -> str:
        """Get comprehensive context for a query using graph RAG."""
        context_parts = []
        
        # 1. Get similar queries
        similar_queries = self.query_graph.get_query_context(query_text)
        if similar_queries:
            context_parts.append("=== Similar Past Queries ===")
            context_parts.append(similar_queries)
        
        # 2. Extract tables from query (if needed)
        if extract_tables:
            tables = self._extract_tables_from_query(query_text)
            if tables:
                context_parts.append("\n=== Schema Context ===")
                schema_context = self.schema_graph.get_schema_context(tables)
                context_parts.append(schema_context)
                
                # Get related tables
                all_tables = set(tables)
                for table in tables:
                    related = self.schema_graph.get_related_tables(table)
                    all_tables.update(related)
                
                if len(all_tables) > len(tables):
                    context_parts.append(f"\nRelated tables: {', '.join(all_tables - set(tables))}")
        
        return "\n".join(context_parts)
    
    def _extract_tables_from_query(self, query_text: str) -> List[str]:
        """Extract table names from query text."""
        # Known tables
        known_tables = ['users', 'orders', 'products', 'order_items', 
                       'inventory_items', 'events', 'distribution_centers']
        
        query_lower = query_text.lower()
        found_tables = []
        for table in known_tables:
            if table in query_lower or table.replace('_', ' ') in query_lower:
                found_tables.append(table)
        
        return found_tables
    
    def add_query_result(self, query_text: str, sql_query: str, 
                        result: Any, entities: List[str] = None):
        """Add a query and its result to the graph."""
        tables = self._extract_tables_from_query(query_text)
        if not entities:
            entities = self.query_graph._extract_entities(query_text)
        
        return self.query_graph.add_query(
            query_text, sql_query, result, entities, tables
        )
    
    def get_join_suggestions(self, tables: List[str]) -> List[Dict]:
        """Get join suggestions based on schema graph."""
        suggestions = []
        
        if len(tables) < 2:
            return suggestions
        
        # Find paths between tables
        for i, table1 in enumerate(tables):
            for table2 in tables[i+1:]:
                path = self.schema_graph.get_join_path(table1, table2)
                if path:
                    suggestions.append({
                        'from': table1,
                        'to': table2,
                        'path': path,
                        'via': self._get_join_columns(table1, table2)
                    })
        
        return suggestions
    
    def _get_join_columns(self, table1: str, table2: str) -> List[str]:
        """Get columns that can be used for joining."""
        join_cols = []
        
        # Check edges between tables
        for edge in self.schema_graph.graph.edges(f"table:{table1}", data=True):
            if edge[1].startswith('table:') and edge[1] == f"table:{table2}":
                via_col = edge[2].get('via_column', '')
                if via_col:
                    join_cols.append(via_col)
        
        return join_cols
    
    def save_graph(self, filepath: str):
        """Save graph to file."""
        graph_data = {
            'schema': nx.node_link_data(self.schema_graph.graph),
            'queries': nx.node_link_data(self.query_graph.graph)
        }
        with open(filepath, 'w') as f:
            json.dump(graph_data, f, indent=2)
    
    def load_graph(self, filepath: str):
        """Load graph from file."""
        with open(filepath, 'r') as f:
            graph_data = json.load(f)
        
        self.schema_graph.graph = nx.node_link_graph(graph_data['schema'])
        self.query_graph.graph = nx.node_link_graph(graph_data['queries'])


# Global instance
_graph_rag_instance = None

def get_graph_rag(db: SQLDatabase = None) -> GraphRAG:
    """Get or create Graph RAG instance."""
    global _graph_rag_instance
    if _graph_rag_instance is None:
        if db is None:
            db = SQLDatabase.from_uri(f"sqlite:///{DATABASE}")
        _graph_rag_instance = GraphRAG(db)
    return _graph_rag_instance

