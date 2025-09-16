


# Demo App – Natural Language Database Query

Ez az alkalmazás lehetővé teszi, hogy egy konfigurálható adatbázishoz csatlakozzunk, és az OpenAI (agent, tools) segítségével szabad szöveges lekérdezéseket futtassunk rajta.  
Az OpenAI látja az adatbázis **sémáját**, a felhasználói igényeket és az esetleges hibákat, de **nem látja a konkrét adatokat** – azokat maga az alkalmazás kérdezi le és jeleníti meg.

## ✨ Fő funkciók
- Adatbázis-kapcsolat konfigurálható módon  
- Szabad szöveges lekérdezések OpenAI agenten keresztül  
- Az agent csak a séma és meta-információk alapján dolgozik  
- A tényleges adatlekérés az alkalmazás feladata  
- Hibakezelés és visszajelzés a felhasználónak

## 📌 Funkcionális követelmények (user sztorik)

- **Felhasználóként** szeretnék természetes nyelven lekérdezéseket feltenni az adatbázisról,  
  **hogy** SQL-ismeret nélkül is gyorsan információhoz jussak.

- **Fejlesztőként** szeretném, hogy az app automatikusan frissítse az adatbázis sémáját,  
  **hogy** új táblák vagy mezők hozzáadásakor azonnal használható legyen.

- **Rendszergazdaként** szeretném konfigurálni, hogy mely adatbázishoz kapcsolódjon az alkalmazás,  
  **hogy** több különböző környezetben is könnyen beállítható legyen.

- **Felhasználóként** szeretném, ha az app megmutatná a lekérdezés eredményét felületen,  
  **hogy** azonnal lássam a választ.

---

## 🛡️ Minőségi követelmények

- Az OpenAI csak a séma- és meta-információkhoz férhet hozzá, az érzékeny adatokhoz nem.
- A hibák egyértelmű, emberi nyelven jelenjenek meg a felhasználók számára.
- A rendszernek stabilan és megbízhatóan kell futnia hosszabb időn át.
- Az alkalmazásnak skálázhatónak kell lennie több párhuzamos felhasználó esetén is.

## 🚀 Hogyan próbálhatod ki?
1. Konfiguráld az adatbázis-kapcsolatot (`.env` vagy config fájl).  
2. Indítsd el az alkalmazást.
3. Írj be egy természetes nyelvű lekérdezést.
4. A beszélgetés addig folytatódik, amíg `exit` (vagy `kilép`) paranccsal ki nem lépsz.
5. Nézd meg az eredményt az app felületén.

### 💬 Chat üzemmód

Az `app.py` mostantól folyamatos párbeszédet kezel:

- az OpenAI-asszisztens három toolt használ: `get_schema`, `run_sql`, `finish`
- a séma lekérése és az SQL futtatása is toolhívással történik
- a felhasználó a `finish` tool hívása után kapja meg az összegzést
- kilépéshez írd be: `exit`, `quit`, `kilép` vagy `kilep`

Konfigurálható modell: `OPENAI_MODEL` (alapértelmezés: `gpt-4o-mini`).

---

## 📚 Demóadatbázis (seed)

Egy összetettebb, valószerű demóadatbázist készítettem SQLite-ban (vásárlók, rendelések, tételek, termékek, alkalmazottak, stb.).

- Fájl: `seed_db.py`  
- Alapértelmezett útvonal: `sample.db` (állítható: `DATABASE_PATH`)

Futtatás:

```
python3 seed_db.py
```

Ez létrehozza és feltölti az adatbázist kb. az alábbiakkal:

- 500 vevő (`customers`)
- 2000 rendelés (`orders`)
- ~6000 rendelés tétel (`order_items`)
- 200 termék (`products`), 8 kategória (`categories`), 12 beszállító (`suppliers`)
- 25 alkalmazott (`employees`)
- 2000 fizetés (`payments`)
- ~600 értékelés (`reviews`)

Hasznos táblák: `customers`, `orders`, `order_items`, `products`, `employees`, `payments`, `reviews`, `categories`, `suppliers`

Minta közvetlen SQL-lekérdezések (OpenAI nélkül):

```
-- Top 10 termék összárbevétel szerint
SELECT p.name, ROUND(SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), 2) AS revenue
FROM order_items oi
JOIN products p ON p.id = oi.product_id
GROUP BY p.id
ORDER BY revenue DESC
LIMIT 10;

-- Havi rendelésdarabszám az elmúlt 12 hónapból
SELECT substr(order_date, 1, 7) AS month, COUNT(*) AS order_count
FROM orders
GROUP BY month
ORDER BY month DESC
LIMIT 12;
```

Ha inkább ismert mintaadatbázist szeretnél (pl. Chinook/Northwind), szólj, be tudom húzni és konvertálni SQLite-ra is.

---

## 📝 Lekérdezés-naplózás

A futtatott SQL-ek JSON-lines formátumban naplózódnak (1 sor = 1 esemény).

- Fájl: alapértelmezetten `queries.log`
- Engedélyezés/tiltás: `LOG_QUERIES` (alap: `1`=engedélyezve)
- Útvonal: `LOG_FILE` (alap: `queries.log`)

Példa naplósor:

```
{"ts":"2025-09-15T16:12:34Z","sql":"SELECT * FROM customers LIMIT 10","rows_count":10,"duration_ms":2.41,"error":null}
```

---

## 🔌 MCP szerver ugyanazokkal a toolokkal

Az `mcp_server.py` egy [Model Context Protocol](https://spec.modelcontextprotocol.io/) szervert indít, amely ugyanazt a két
toolt (`get_schema`, `run_sql`) teszi elérhetővé, mint a CLI alkalmazás. Így a demóadatbázis távolról is integrálható MCP-
kompatibilis kliensekbe.

Használat:

```bash
pip install -r requirements.txt  # szükséges a `mcp` csomag is
export DATABASE_PATH=sample.db   # vagy a saját SQLite fájlod
python3 mcp_server.py
```

A szerver minden híváshoz új SQLite-kapcsolatot nyit, így több párhuzamos kérésre is biztonságosan reagál.
