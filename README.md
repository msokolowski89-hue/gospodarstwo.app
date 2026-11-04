# Zarządzanie gospodarstwem

Aplikacja do ewidencji pól, upraw i zabiegów agrotechnicznych według sezonów (płodozmian, koszty, bilans azotu).
Strona działa na **GitHub Pages**, dane są w **Firebase Firestore**, logowanie kontem **Google**.

W tym repozytorium jest tylko kod. Dane gospodarstwa nie trafiają na GitHub. Są w Firebase, a dostęp mają tylko konta wpisane w regułach.

## Pliki

| Plik | Do czego służy |
|---|---|
| `index.html` | cała aplikacja |
| `firebase-config.js` | adres Twojego projektu Firebase (do uzupełnienia, krok 1) |
| `firestore.rules` | reguły dostępu do danych (wzór, krok 2) |

## Krok 1. Projekt Firebase

1. Wejdź na https://console.firebase.google.com i zaloguj się kontem Google.
2. **Utwórz projekt**, np. o nazwie `gospodarstwo`. Google Analytics możesz wyłączyć.
3. Po lewej wybierz **Kompilacja → Firestore Database → Utwórz bazę danych**:
   - lokalizacja: `eur3 (Europe)` albo `europe-central2 (Warszawa)`,
   - tryb: **produkcyjny**.
4. Wybierz **Kompilacja → Authentication → Rozpocznij → Google → Włącz**, podaj swój e-mail i zapisz.
5. Kliknij **koło zębate → Ustawienia projektu → Twoje aplikacje → ikona `</>` (Aplikacja internetowa)**:
   - nadaj nazwę, np. `www`,
   - Firebase Hosting **nie** jest potrzebny,
   - Firebase pokaże blok `firebaseConfig`. Przepisz te wartości do pliku `firebase-config.js`.

## Krok 2. Reguły dostępu

W **Firestore Database → Reguły** wklej zawartość `firestore.rules`. Zamiast `TWOJ_EMAIL@gmail.com` wpisz swój adres i ewentualnie adresy pracowników, np.:

```
request.auth.token.email in ['ja@gmail.com', 'pracownik@gmail.com'];
```

Kliknij **Opublikuj**.

## Krok 3. GitHub Pages

1. Na github.com utwórz **nowe repozytorium**, np. `gospodarstwo`:
   - ma być **publiczne**, bo darmowe GitHub Pages działa tylko dla publicznych repozytoriów; danych w nim nie ma,
   - bez README i bez .gitignore.
2. Wyślij ten folder do repozytorium. W Terminalu, w tym folderze, wpisz:
   ```
   git remote add origin https://github.com/msokolowski89-hue/gospodarstwo.app.git
   git push -u origin main
   ```
   Przy pierwszym wysłaniu macOS zapyta o login GitHub. Jako hasło podaj **token**, nie hasło do konta. Token tworzysz w GitHub → Settings → Developer settings → Personal access tokens. Możesz też zamiast tego użyć programu **GitHub Desktop**.
3. W repozytorium wejdź w **Settings → Pages**:
   - **Source: Deploy from a branch**,
   - **Branch: `main` / `(root)`**,
   - kliknij **Save**.

   Po około minucie strona będzie pod adresem `https://msokolowski89-hue.github.io/gospodarstwo.app/`.
4. W Firebase wejdź w **Authentication → Ustawienia → Autoryzowane domeny → Dodaj domenę** i wpisz `msokolowski89-hue.github.io`.

## Krok 4. Przeniesienie danych

1. Otwórz stronę i zaloguj się przez Google.
2. Kliknij **Import** u góry i wybierz plik `gospodarstwo-dane.json`. Plik leży w Dokumentach, poza tym repozytorium.

Przycisk **Kopia danych** pobiera aktualną kopię wszystkich danych do pliku JSON. Rób ją co jakiś czas.

## Zmiany w aplikacji

Edytuj `index.html`, potem:

```
git add -A
git commit -m "Opis zmiany"
git push
```

Po około minucie nowa wersja jest na stronie.
