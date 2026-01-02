#!/usr/bin/env python3
"""
Script de migración para agregar campos sender_email y sender_name a la tabla campaigns.
Ejecutar una sola vez después de actualizar el código.
"""

from app import app, db
from sqlalchemy import text

def migrate():
    """Agrega los campos sender_email y sender_name a la tabla campaigns"""
    with app.app_context():
        try:
            # Verificar si las columnas ya existen
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('campaigns')]
            
            if 'sender_email' not in columns:
                print("Agregando columna sender_email...")
                db.session.execute(text("ALTER TABLE campaigns ADD COLUMN sender_email VARCHAR(320)"))
                db.session.commit()
                print("✓ Columna sender_email agregada")
            else:
                print("✓ Columna sender_email ya existe")
            
            if 'sender_name' not in columns:
                print("Agregando columna sender_name...")
                db.session.execute(text("ALTER TABLE campaigns ADD COLUMN sender_name VARCHAR(200)"))
                db.session.commit()
                print("✓ Columna sender_name agregada")
            else:
                print("✓ Columna sender_name ya existe")
            
            print("\n✅ Migración completada exitosamente!")
            
        except Exception as e:
            print(f"❌ Error durante la migración: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()
