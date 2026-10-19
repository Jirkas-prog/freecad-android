# FreeCAD + FusionFlow pro Android

**[Stáhnout APK](https://github.com/Jirkas-prog/freecad-android/releases/download/v0.1.0-alpha.1/FreeCAD-FusionFlow.apk)**

Experimentální offline aplikace obsahuje FreeCAD 1.1.3 a naši nadstavbu FusionFlow
0.20.0. Po instalaci se prostředí zapne automaticky. Výpočty probíhají v tabletu
pomocí WebAssembly, Pythonu a Open CASCADE; aplikace nepotřebuje vzdálený počítač.
Nejde o nativní ARM64 kompilaci celého FreeCADu.

## Instalace

1. Stáhni APK a otevři ho. Povol instalaci z daného prohlížeče nebo správce souborů,
   pokud si ji Android vyžádá.
2. Spusť **FreeCAD · FusionFlow**. První start může trvat déle než minutu.
3. V **DESIGN → Input** vyber **Touch / pen** nebo **Mouse / trackpad**.
4. Soubory otevírej přes **File → Open** nebo **Ctrl+O**. Ukládání přes **Ctrl+S**
   nabídne systémový dialog pro export do vybrané složky.

Není nutné samostatně instalovat FreeCAD ani FusionFlow. Aplikace má celý CAD engine
v APK a nežádá oprávnění k internetu. Výběr cloudového úložiště v systémovém dialogu
může používat síť prostřednictvím příslušného poskytovatele.

## Kompatibilita

Android 10+ a novější WebView s podporou izolovaných originů, memory64, JSPI,
sdílené paměti a WebGL2. Samotné číslo Androidu kompatibilitu nezaručuje. Pokud se
objeví **WebView update required**, aktualizuj Android System WebView běžnou cestou.
Jestli potřebná funkce v tvé verzi ještě není, aplikace na ní zatím nepoběží.

Ověřeno v emulátoru Android 15, x86_64, s WebView **158.0.8113.0**. Skutečný Samsung
Galaxy Tab S9 zatím ověřen nebyl. Doporučení 8 GB RAM a 2 GB volného místa je odhad
pro menší modely, nikoli naměřená hardwarová záruka.

## Na co myslet

- Jde o **alfa verzi**. Používej kopie důležitých modelů a pravidelně exportuj.
- Obnova rozpracované relace je v soukromých datech aplikace. Odinstalace nebo
  vymazání dat ji odstraní. Exportované soubory v jiné složce zůstávají samostatné.
- Dotykové ovládání má klepnutí pro výběr, jeden prst pro otáčení, dva pro posun a
  gesto sevření pro zoom. Nástroje skici používají klepnutí jako zadávání bodů.
- Specifické funkce S Penu, odmítání dlaně, tlak pera a Samsung DeX nejsou
  hardwarově otestované. Klávesnice a touchpad jsou pro přesné kreslení vhodné.
- Externí FEM řešiče, online instalace dalších doplňků a serverová spolupráce nejsou
  součástí tohoto balíku. Ne všechny příkazy všech workbenchů byly ověřeny.

[Podrobný popis, sestavení a omezení](../README.md) ·
[Provedené testy](VERIFICATION.md) · [Licence a původ kódu](../NOTICE.md)
