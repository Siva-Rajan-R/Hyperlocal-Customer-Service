import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:TempSuperSecretPwd@89.167.72.254:5432/CustomerServiceDb')
    await conn.execute('ALTER TABLE customers ALTER COLUMN ui_id DROP IDENTITY IF EXISTS')
    await conn.execute('ALTER TABLE customers ALTER COLUMN ui_id TYPE VARCHAR USING ui_id::VARCHAR')
    print('Altered customers table!')
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
