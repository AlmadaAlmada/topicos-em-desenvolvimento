from app.ai.rules import apply_floor, priority_floor
from app.ai.text import normalize


def test_normalize_removes_accents_and_unifies_synonyms():
    assert normalize("Wi-Fi não conecta no E-mail") == "wifi nao conecta email"


def test_personal_data_is_masked_before_ai():
    out = normalize("Meu email é joao.silva@empresa.com, CPF 123.456.789-00, tel (71) 99876-5432")
    assert "joao" not in out and "123" not in out and "99876" not in out
    assert "dadoemail" in out and "dadocpf" in out and "dadotelefone" in out


def test_priority_floor_only_raises():
    assert apply_floor("Baixa", "Crítica") == "Crítica"
    assert apply_floor("Crítica", "Alta") == "Crítica"
    assert apply_floor("Média", None) == "Média"


def test_priority_rules():
    assert priority_floor("Vírus", "antivírus detectou ransomware")[0] == "Crítica"
    assert priority_floor("Sem rede", "todos os computadores do setor sem rede")[0] == "Crítica"
    assert priority_floor("Excel", "não consigo trabalhar, o excel fecha")[0] == "Alta"
    # "todos" sozinho, sem indicar impacto, não deve disparar a regra
    assert priority_floor("Word", "como imprimir todos os slides")[0] is None
