#!/usr/bin/env python3
"""
Vector Ingestion & Hybrid Retrieval Flow Demo
==============================================

This script demonstrates:
1. Ingestion Pipeline: JSON → Embeddings → DB2 Storage
2. Pure Vector Search: Query → Embedding → Similarity Search
3. Hybrid Search: Query → Embedding + SQL Filters → Filtered Results

Requirements:
- DB2 database with vector support
- db2_config.json with connection details
- Python packages: ibm-db, sentence-transformers
"""

import json
import sys
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import ibm_db

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("❌ Error: sentence-transformers not installed")
    print("Install with: pip install sentence-transformers")
    sys.exit(1)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class DB2Config:
    """DB2 connection configuration"""
    database: str
    hostname: str
    port: int
    username: str
    password: str
    
    @classmethod
    def from_file(cls, filepath: str = "db2_config.json") -> "DB2Config":
        """Load configuration from JSON file"""
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
            return cls(**config)
        except FileNotFoundError:
            print(f"❌ Error: {filepath} not found")
            print("Create it from db2_config.example.json")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            sys.exit(1)


# ============================================================================
# Database Connection
# ============================================================================

class DB2Connection:
    """Manages DB2 database connection"""
    
    def __init__(self, config: DB2Config):
        self.config = config
        self.conn = None
        
    def connect(self) -> bool:
        """Establish connection to DB2"""
        try:
            conn_str = (
                f"DATABASE={self.config.database};"
                f"HOSTNAME={self.config.hostname};"
                f"PORT={self.config.port};"
                f"PROTOCOL=TCPIP;"
                f"UID={self.config.username};"
                f"PWD={self.config.password};"
            )
            self.conn = ibm_db.connect(conn_str, "", "")
            print("✅ Connected to DB2")
            return True
        except Exception as e:
            print(f"❌ DB2 connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close DB2 connection"""
        if self.conn:
            ibm_db.close(self.conn)
            print("✅ Disconnected from DB2")
    
    def execute(self, sql: str, params: Optional[tuple] = None) -> Any:
        """Execute SQL statement"""
        try:
            stmt = ibm_db.prepare(self.conn, sql)
            if params:
                for i, param in enumerate(params, 1):
                    ibm_db.bind_param(stmt, i, param)
            ibm_db.execute(stmt)
            return stmt
        except Exception as e:
            print(f"❌ SQL execution failed: {e}")
            print(f"SQL: {sql}")
            raise
    
    def fetch_all(self, stmt) -> List[Dict[str, Any]]:
        """Fetch all results from statement"""
        results = []
        row = ibm_db.fetch_assoc(stmt)
        while row:
            results.append(dict(row))
            row = ibm_db.fetch_assoc(stmt)
        return results


# ============================================================================
# Embedding Model
# ============================================================================

class EmbeddingModel:
    """Handles text embedding generation"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding model"""
        print(f"📦 Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded (dimension: {self.dimension})")
    
    def encode(self, text: str) -> List[float]:
        """Generate embedding for text"""
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return [emb.tolist() for emb in embeddings]


# ============================================================================
# Database Schema Setup
# ============================================================================

class SchemaManager:
    """Manages database schema for products table"""
    
    def __init__(self, db: DB2Connection, embedding_dim: int):
        self.db = db
        self.embedding_dim = embedding_dim
        self.table_name = "PRODUCTS"
    
    def create_table(self):
        """Create products table with vector column"""
        print(f"\n📋 Creating table: {self.table_name}")
        
        # Drop existing table
        try:
            drop_sql = f"DROP TABLE {self.table_name}"
            self.db.execute(drop_sql)
            print(f"✅ Dropped existing table")
        except:
            pass  # Table doesn't exist
        
        # Create new table
        create_sql = f"""
        CREATE TABLE {self.table_name} (
            PRODUCT_ID INTEGER NOT NULL PRIMARY KEY,
            PRICE DECIMAL(10,2),
            DESCRIPTION VARCHAR(5000),
            EMBEDDING_VECTOR VECTOR({self.embedding_dim})
        )
        """
        self.db.execute(create_sql)
        print(f"✅ Table created with vector dimension {self.embedding_dim}")


# ============================================================================
# Ingestion Pipeline
# ============================================================================

class IngestionPipeline:
    """Handles data ingestion from JSON to DB2"""
    
    def __init__(self, db: DB2Connection, embedder: EmbeddingModel):
        self.db = db
        self.embedder = embedder
        self.table_name = "PRODUCTS"
    
    def ingest_products(self, products: List[Dict[str, Any]]):
        """
        Ingest products with embeddings
        
        Flow:
        JSON Data → Extract description → Generate embedding → Insert to DB2
        """
        print(f"\n📥 Starting ingestion of {len(products)} products")
        
        for i, product in enumerate(products, 1):
            product_id = product['product_id']
            price = product['price']
            description = product['description']
            
            # Generate embedding
            print(f"  [{i}/{len(products)}] Generating embedding for product {product_id}...")
            embedding = self.embedder.encode(description)
            embedding_str = str(embedding).replace('[', '{').replace(']', '}')
            
            # Insert into DB2
            insert_sql = f"""
            INSERT INTO {self.table_name} 
            (PRODUCT_ID, PRICE, DESCRIPTION, EMBEDDING_VECTOR)
            VALUES (?, ?, ?, VECTOR(?))
            """
            
            try:
                self.db.execute(insert_sql, (product_id, price, description, embedding_str))
                print(f"  ✅ Product {product_id} ingested")
            except Exception as e:
                print(f"  ❌ Failed to ingest product {product_id}: {e}")
        
        print(f"✅ Ingestion complete")


# ============================================================================
# Retrieval Pipeline
# ============================================================================

class RetrievalPipeline:
    """Handles vector and hybrid search queries"""
    
    def __init__(self, db: DB2Connection, embedder: EmbeddingModel):
        self.db = db
        self.embedder = embedder
        self.table_name = "PRODUCTS"
    
    def vector_search(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Pure vector similarity search
        
        Flow:
        Query → Generate embedding → Similarity search → Top-K results
        """
        print(f"\n🔍 Vector Search: '{query_text}'")
        print(f"   Top-K: {top_k}")
        
        # Generate query embedding
        query_embedding = self.embedder.encode(query_text)
        embedding_str = str(query_embedding).replace('[', '{').replace(']', '}')
        
        # Vector similarity search
        search_sql = f"""
        SELECT 
            PRODUCT_ID,
            PRICE,
            DESCRIPTION,
            VECTOR_DISTANCE(EMBEDDING_VECTOR, VECTOR(?), COSINE) AS DISTANCE
        FROM {self.table_name}
        ORDER BY DISTANCE
        FETCH FIRST ? ROWS ONLY
        """
        
        stmt = self.db.execute(search_sql, (embedding_str, top_k))
        results = self.db.fetch_all(stmt)
        
        print(f"✅ Found {len(results)} results")
        return results
    
    def hybrid_search(
        self, 
        query_text: str, 
        price_gte: Optional[float] = None,
        price_lt: Optional[float] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search: Vector similarity + SQL filters
        
        Flow:
        Query → Generate embedding → Vector search + SQL WHERE → Filtered Top-K
        """
        print(f"\n🔍 Hybrid Search: '{query_text}'")
        print(f"   Filters: price >= {price_gte}, price < {price_lt}")
        print(f"   Top-K: {top_k}")
        
        # Generate query embedding
        query_embedding = self.embedder.encode(query_text)
        embedding_str = str(query_embedding).replace('[', '{').replace(']', '}')
        
        # Build WHERE clause
        where_clauses = []
        params = [embedding_str]
        
        if price_gte is not None:
            where_clauses.append("PRICE >= ?")
            params.append(price_gte)
        
        if price_lt is not None:
            where_clauses.append("PRICE < ?")
            params.append(price_lt)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Hybrid search query
        search_sql = f"""
        SELECT 
            PRODUCT_ID,
            PRICE,
            DESCRIPTION,
            VECTOR_DISTANCE(EMBEDDING_VECTOR, VECTOR(?), COSINE) AS DISTANCE
        FROM {self.table_name}
        WHERE {where_sql}
        ORDER BY DISTANCE
        FETCH FIRST ? ROWS ONLY
        """
        
        params.append(top_k)
        stmt = self.db.execute(search_sql, tuple(params))
        results = self.db.fetch_all(stmt)
        
        print(f"✅ Found {len(results)} results")
        return results


# ============================================================================
# Demo Runner
# ============================================================================

class VectorHybridDemo:
    """Main demo orchestrator"""
    
    def __init__(self):
        self.config = DB2Config.from_file()
        self.db = DB2Connection(self.config)
        self.embedder = None
        self.schema_manager = None
        self.ingestion = None
        self.retrieval = None
    
    def setup(self):
        """Initialize all components"""
        print("=" * 70)
        print("Vector Ingestion & Hybrid Retrieval Demo")
        print("=" * 70)
        
        # Connect to DB2
        if not self.db.connect():
            sys.exit(1)
        
        # Load embedding model
        self.embedder = EmbeddingModel()
        
        # Initialize components
        self.schema_manager = SchemaManager(self.db, self.embedder.dimension)
        self.ingestion = IngestionPipeline(self.db, self.embedder)
        self.retrieval = RetrievalPipeline(self.db, self.embedder)
    
    def run_ingestion_demo(self):
        """Demo: Ingestion Pipeline"""
        print("\n" + "=" * 70)
        print("PART 1: INGESTION PIPELINE")
        print("=" * 70)
        
        # Sample product data
        products = [
            {
                "product_id": 1,
                "price": 100,
                "description": "High-quality wireless headphones with noise cancellation. Perfect for music lovers and professionals who need focus. Features 30-hour battery life and premium sound quality."
            },
            {
                "product_id": 2,
                "price": 200,
                "description": "Professional laptop stand with ergonomic design. Adjustable height and angle for comfortable working. Made from premium aluminum with excellent build quality."
            },
            {
                "product_id": 3,
                "price": 400,
                "description": "Smart fitness tracker with heart rate monitoring. Tracks steps, calories, sleep patterns, and workouts. Water-resistant with 7-day battery life and mobile app integration."
            }
        ]
        
        # Create table
        self.schema_manager.create_table()
        
        # Ingest products
        self.ingestion.ingest_products(products)
    
    def run_vector_search_demo(self):
        """Demo: Pure Vector Search"""
        print("\n" + "=" * 70)
        print("PART 2: PURE VECTOR SIMILARITY SEARCH")
        print("=" * 70)
        
        query = "audio equipment for music"
        results = self.retrieval.vector_search(query, top_k=3)
        
        print("\n📊 Results:")
        for i, result in enumerate(results, 1):
            print(f"\n  Rank {i}:")
            print(f"    Product ID: {result['PRODUCT_ID']}")
            print(f"    Price: ${result['PRICE']}")
            print(f"    Distance: {result['DISTANCE']:.4f}")
            print(f"    Description: {result['DESCRIPTION'][:100]}...")
    
    def run_hybrid_search_demo(self):
        """Demo: Hybrid Search (Vector + SQL Filters)"""
        print("\n" + "=" * 70)
        print("PART 3: HYBRID SEARCH (Vector + SQL Filters)")
        print("=" * 70)
        
        query = "health and fitness device"
        results = self.retrieval.hybrid_search(
            query_text=query,
            price_gte=200,
            price_lt=500,
            top_k=3
        )
        
        print("\n📊 Results:")
        for i, result in enumerate(results, 1):
            print(f"\n  Rank {i}:")
            print(f"    Product ID: {result['PRODUCT_ID']}")
            print(f"    Price: ${result['PRICE']}")
            print(f"    Distance: {result['DISTANCE']:.4f}")
            print(f"    Description: {result['DESCRIPTION'][:100]}...")
    
    def cleanup(self):
        """Cleanup resources"""
        self.db.disconnect()
    
    def run(self):
        """Run complete demo"""
        try:
            self.setup()
            self.run_ingestion_demo()
            self.run_vector_search_demo()
            self.run_hybrid_search_demo()
            
            print("\n" + "=" * 70)
            print("✅ Demo completed successfully!")
            print("=" * 70)
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Demo interrupted by user")
        except Exception as e:
            print(f"\n\n❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point"""
    demo = VectorHybridDemo()
    demo.run()


if __name__ == "__main__":
    main()

# Made with Bob
