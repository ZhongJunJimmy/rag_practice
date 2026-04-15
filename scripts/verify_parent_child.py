import os
import sys
from libs.db import get_conn, put_conn

def verify():
    output_path = "verify_output.txt"
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Count chunks with parents
            cur.execute("SELECT COUNT(*) FROM chunks WHERE parent_id IS NOT NULL")
            child_count = cur.fetchone()[0]
            
            # Count total chunks
            cur.execute("SELECT COUNT(*) FROM chunks")
            total_count = cur.fetchone()[0]
            
            output = []
            output.append(f"Total chunks: {total_count}")
            output.append(f"Chunks with parents: {child_count}")
            
            if child_count > 0:
                # Sample a child and its parent
                cur.execute("SELECT id, chunk_id, parent_id, text FROM chunks WHERE parent_id IS NOT NULL LIMIT 1")
                child = cur.fetchone()
                if child:
                    child_id, child_chunk_id, parent_id, child_text = child
                    cur.execute("SELECT chunk_id, text FROM chunks WHERE id = %s", (parent_id,))
                    parent = cur.fetchone()
                    if parent:
                        parent_chunk_id, parent_text = parent
                        output.append("\n--- Sample Parent-Child Relationship ---")
                        output.append(f"Child ID: {child_id} (Chunk ID: {child_chunk_id})")
                        output.append(f"Parent ID: {parent_id} (Chunk ID: {parent_chunk_id})")
                        output.append(f"Child Text (first 50 chars): {child_text[:50]}...")
                        output.append(f"Parent Text (first 50 chars): {parent_text[:50]}...")
                        output.append("----------------------------------------")
            else:
                output.append("\nNo child chunks found with parent_id. Indexing might have failed or structure is not as expected.")
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(output))
        put_conn(conn)
    except Exception as e:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"ERROR: {str(e)}")
            import traceback
            f.write("\n" + traceback.format_exc())

if __name__ == "__main__":
    verify()