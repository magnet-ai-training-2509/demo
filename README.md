


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
4. Nézd meg az eredményt az app felületén.