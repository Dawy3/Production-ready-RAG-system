from ..vectorDB_interface import VectorDBInterface
from ..vectorDB_enums import DistanceMethodEnums, PgVectorTableSchemeEnums, PgVectorDistanceMethodEnums, PgVectorIndexTypeEnums
import logging
from typing import List
from db_models.db_schemes import RetrievedDocument
from sqlalchemy.sql import text as sql_text
import json


class PGVectorProvider(VectorDBInterface):
    
    def __init__(self, db_client, default_vector_size: int = 786,
                distance_method: str= None):
        self.db_client = db_client
        self.default_vector_size = default_vector_size
        self.distance_method = distance_method
        
        self.pgvector_table_prefix = PgVectorTableSchemeEnums._PREFIX.value
        
        self.logger = logging.getLogger("uvicorn")
        
        
    async def connect(self):
        async with self.db_client as session:
            async with session.begin():
                await session.execute(sql_text(
                    "CREATE EXTENSION IF NOT EXISTS vector"
                ))
            await session.commit()
    
    async def disconnect(self):
        pass
    
    async def is_collection_existed(self, collection_name: str) -> bool:
        
        record = None
        async with self.db_client as session:
            async with session.begin():
                t = sql_text("SELECT * FROM pg_tables WHERE tablename = :collection_name")
                results  = await session.execute(t, {"collection_name" : collection_name})
                record = results.scalar_one_or_none()
                
        return record
    
    async def list_all_collection(self) -> List:
        records = []
        async with self.db_client as session:
            async with session.begin():
                t = sql_text("SELECT tablename FROM pg_tables WHERE tablename LIKE :prefix")
                results = await session.execute(t, {"prefix": self.pgvector_table_prefix})
                records = results.scalars().all()
        
        return records
    
    async def get_collection_info(self, collection_name: str) -> dict:
        async with self.db_client as session:
            async with session.begin():
                t = sql_text('''
                    SELECT schemaname, tablename, tableowner, tablespace, hasindexes
                    FROM pg_tables
                    WHERE tablename = :collection_name
                ''')
                count_sql = sql_text(f"SELECT COUNT(*) FROM :collection_name")
                
                table_info = await session.execute(t, {"collection_name": collection_name})
                record_count = await session.execute(count_sql, {"collection_name": collection_name})
                
                table_data = table_info.fetchone()
                if not table_data:
                    return None
                
                return {
                    "table_info" : dict(table_data),
                    "record_count" : record_count
                }
                
    async def delete_collection(self, collection_name: str):
        async with self.db_client as session:
            async with session.begin():
                self.logger.info(f"Deleting collection: {collection_name}")
                delete_sql = sql_text("DROP TABLE IF EXISTS :collection_name")
                await session.execute(delete_sql, {"collection_name": collection_name})
                await session.commit()
                
        return True
    
    async def create_collection(self, collection_name: str,
                                embedding_size: int,
                                do_reset: bool = False):
                
        if do_reset:
            _ = await self.delete_collection(collection_name)
            
        is_collection_existed = await self.is_collection_existed(collection_name)
        if not is_collection_existed:
            self.logger.info(f"Creating Collection: {collection_name}")
            async with self.db_client as session:
                async with session.begin():
                    t = sql_text(
                        "CREATE TABLE :collection_name ("
                            f'{PgVectorTableSchemeEnums.ID.value} bigserial PRIMARY KEY'
                            f'{PgVectorTableSchemeEnums.TEXT.value} text, '
                            f'{PgVectorTableSchemeEnums.VECTOR.value} vector({embedding_size}), '
                            f'{PgVectorTableSchemeEnums.METADATA.value} jsonb DEFAULT \'{{}}\', '
                            f'{PgVectorTableSchemeEnums.CHUNK_ID.value} integer, '
                            f'FOREIGN KEY ({PgVectorTableSchemeEnums.CHUNK_ID.value}) REFERANCES chunks(chunk_id)'
                        ")"
                    )
                    await session.execute(t)
                    await session.commit()
                    
            return True
        
        return False
    