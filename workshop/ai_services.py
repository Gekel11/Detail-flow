import os
import re
from google import genai
from .models import CarBlueprint

def get_or_generate_blueprint(make: str, model: str) -> str:
    """
    Pobiera schemat z bazy danych lub generuje precyzyjny kod 5 rzutów SVG przez Gemini.
    """
    # 1. Sprawdź cache w bazie
    cached = CarBlueprint.objects.filter(make__iexact=make, model__iexact=model).first()
    if cached:
        return cached.svg_code

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Brak zdefiniowanego GEMINI_API_KEY w pliku .env!")

    client = genai.Client(api_key=api_key)

    prompt = f"""
Jesteś precyzyjnym systemem CAD w studio detailingowym.
Wygeneruj WNĘTRZE kodu SVG z technicznym rzutem 5 stron pojazdu: {make} {model}.

Ścisłe reguły techniczne:
- Wymiary planszy: viewBox 0 0 1000 640.
- Stylistyka: CAD / Technical Drawing na ciemnym tle.
- Użyj atrybutów: stroke="#71717a" stroke-width="1.5", wypełnienia: fill="#18181b" lub fill="#09090b".
- Linie przetłoczeń, reflektory, charakterystyczny grill/pas przedni i tylny charakterystyczne dla {make} {model}.

Musisz podzielić rysunek dokładnie na 5 grup z podanymi ID:
1. <g id="zone-FRONT">: Przód auta w obrysie x:30, y:30, szerokość:280, wysokość:240. Etykieta text: "// 01. PRZÓD ({make} {model})"
2. <g id="zone-TOP">: Rzut z góry na środku w obrysie x:330, y:30, szerokość:340, wysokość:580 (maska, dach, szyby, klapa). Etykieta text: "// 02. RZUT Z GÓRY"
3. <g id="zone-REAR">: Tył auta w obrysie x:690, y:30, szerokość:280, wysokość:240 (lampy, wydechy, dyfuzor). Etykieta text: "// 03. TYŁ"
4. <g id="zone-LEFT">: Lewy bok pojazdu w obrysie x:30, y:290, szerokość:280, wysokość:320 (koła, linia okien, drzwi). Etykieta text: "// 04. LEWY BOK"
5. <g id="zone-RIGHT">: Prawy bok pojazdu w obrysie x:690, y:290, szerokość:280, wysokość:320. Etykieta text: "// 05. PRAWY BOK"

Odpowiedz WYŁĄCZNIE czystym kodem wektorowym XML/SVG (same elementy <g>, <path>, <rect>, <polygon>, <text> bez zewnętrznego tagu <svg> i bez znaczników markdown ```).
"""

    response = client.models.generate_content(
        model='gemini-3.6-flash',
        contents=prompt
    )

    clean_svg = response.text.strip()
    clean_svg = re.sub(r"^```(?:xml|svg)?", "", clean_svg, flags=re.MULTILINE)
    clean_svg = re.sub(r"```$", "", clean_svg, flags=re.MULTILINE).strip()

    # Zapisz do cache
    blueprint = CarBlueprint.objects.create(
        make=make,
        model=model,
        svg_code=clean_svg
    )

    return clean_svg
