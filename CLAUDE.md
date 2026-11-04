# Zarządzanie gospodarstwem – kontekst projektu

Aplikacja do ewidencji pól, upraw i zabiegów agrotechnicznych gospodarstwa rolnego (34 pola, ok. 93 ha).
Odpowiadaj po polsku. Użytkownik nie jest programistą: tłumacz kroki prosto, komendy dawaj gotowe do wklejenia.

## Dwie wersje tej samej aplikacji

| Wersja | Gdzie | Dane |
|---|---|---|
| **GitHub Pages** (docelowa) | https://msokolowski89-hue.github.io/gospodarstwo.app/ – repo `msokolowski89-hue/gospodarstwo.app`, gałąź `main`, katalog główny | Firebase Firestore, projekt `gospodarstwo-720d7`, logowanie Google |
| **Artefakt claude.ai** (pierwsza wersja) | https://claude.ai/artifact/TAcudyTbptgv3EYPv11Y45 | baza artefaktu (capability `db`), edytowana narzędziem ArtifactData |

Źródłem jest `zrodla/claude-artifact.html` (wersja claude.ai: `window.claude.use("db")`, `user`, `downloads`).
`index.html` **generuje się** z niego skryptem `zrodla/build_www.py`. Skrypt podmienia start aplikacji na Firebase compat SDK 10.12.2 (logowanie Google, import i kopia JSON, `enablePersistence` do pracy offline).
Zmiany w aplikacji: edytuj `zrodla/claude-artifact.html` → `cd zrodla && python3 build_www.py` → commit → `git push`. Jeśli artefakt w claude.ai ma też dostać zmianę, opublikuj go ponownie pod tym samym URL.
Push wymaga tokenu GitHub z pęku kluczy macOS. Uruchamiaj go w panelu Terminal (`run_in_terminal`), bo w razie potrzeby użytkownik sam wpisuje dane logowania.

## Model danych (Firestore i baza artefaktu – identyczny)

- `pola/{slug}`: `nazwa, dzialki, ident, ha, klasa, ph, p2o5, k2o, analiza (YYYY-MM-DD), wlasnosc, uwagi`. Id to slug nazwy, np. `ae-zocha`.
- `uprawy/{poleId}_{rok}`: `pole, rok, uprawa, odmiana, status (Plan | W trakcie | Zrealizowane), siew, norma, zbior, plon, uwagi`.
- `zabiegi/{id}`: `data, rok, pole, rodzaj, typ, srodek, dawka, jedn, ha (null = całe pole), cena, bbch, pogoda, wykonawca, uwagi, N, P, K, S, Mg`. Przy siewie dodatkowo `gatunek, odmiana, rosliny: [{gatunek, odmiana, dawka}]`. Zabiegi z eAgronom mają id `ea-RRRR-NNN`.

## Zasady dziedzinowe (ustalone z użytkownikiem)

- **Sezon** zapisuje się jako rok zbioru (`rok`), a wyświetla jako `rok-1/rok`, np. 2026 → „2025/2026”. Oziminy siane jesienią należą do następnego sezonu.
- **Siew** (Siew uprawy głównej, Siew agregatem uprawowo-siewnym, Siew międzyplonu, Sadzenie): siew od lipca dostaje automatycznie następny sezon. Formularz ma listę roślin (gatunek, odmiana, norma), a normy się sumują. Siew uprawy głównej może zapisać też uprawę pola (pole wyboru „Zapisz też jako uprawę”).
- **Rodzaje zabiegów** mają nazwy jak w eAgronom (Oprysk, Nawożenie, Rozlewanie gnojowicy/gnojówki/pofermentu, Rozrzucanie obornika, Siew uprawy głównej…). Typ środka (Herbicyd, Adiuwant, Nawóz mineralny stały, Nawóz naturalny płynny, Nasiona…) jest w osobnym polu `typ`.
- **Azot z nawozów naturalnych** (limit 170 kg N/ha średnio w gospodarstwie) liczy funkcja `isOrganic`: rodzaj, typ lub środek zawiera gnojowica/obornik/naturalny/poferment.
- Uprawy wieloletnie (TUZ, trawy, mieszanki traw, lucerna, koniczyna) nie dostają ostrzeżenia „ta sama uprawa po sobie”.
- Tabele Pola, Uprawy, Zabiegi i Podsumowanie da się sortować (nagłówki i lista „Sortuj”, ustawienie zapamiętane w localStorage).

## Import z eAgronom

Eksport „crop protection plan” (.xls, jeden arkusz na pole, wiersz 0 to „Sezon RRRR/RR”, zabiegi od wiersza 15).
Parser: `zrodla/import_eagronom.py` (wymaga `xlrd`). Ustalenia:
- Część pól miała w sezonie 2024/25 inne nazwy w eAgronom („Żuk 1” → Y - Żuk 1, „Zocha” → AE…). Dopasowuj je po numerach działek.
- Chmielowe-1 i Chmielowe-2 to dziś jedno pole AH.
- Działki Krahlowe (174, 175) użytkownik kazał pominąć.
- Zawsze najpierw sprawdź, czy plik nie jest duplikatem już wgranego sezonu (`cmp`).

## Wgrane dane (stan na 2026-11-04)

Sezony 2024/2025 (30 upraw, 39 zabiegów), 2025/2026 (34 uprawy, 117 zabiegów) i 2026/2027 (plan plus siew pszenżyta Borowik C2 z 04.11.2026 na 8 polach).
Pełna kopia: `~/Documents/gospodarstwo-dane.json`. Plik jest poza repozytorium, bo repozytorium jest publiczne i nie może zawierać danych gospodarstwa.
Reguły Firestore z adresem użytkownika: `~/Documents/gospodarstwo-reguly-firestore.txt` (w repo jest wzór `firestore.rules`).

## Otwarte sprawy

- Pole K - Zygmuntowie: eAgronom podaje raz działkę `32/2`, raz `32`. Użytkownik nie rozstrzygnął, w aplikacji jest `32/2`.
- Analiza gleby (P₂O₅ 159,1, K₂O 222,9) jest identyczna dla wszystkich pól, prawdopodobnie to średnia z eAgronom.
- Brak cen środków, plonów i dat zbioru, więc koszty są puste.
