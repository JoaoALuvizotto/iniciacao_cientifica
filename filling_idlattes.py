"""
Preenchedor de IDs Lattes para Pesquisadores e Coautores da Rede.
Abordagem direta e simples:
1. Constrói um índice (nome normalizado -> id_lattes) usando o nome completo e
   as citações bibliográficas (listaNomesCitacao) de cada pesquisador da rede.
2. Percorre as produções e orientações de cada currículo.
3. Se um coautor ou orientado pertencer à rede, preenche seu id_lattes ausente.

Uso:
    python filling_idlattes.py [--folder curriculos_json] [--log filled_idlattes_log.csv]
"""

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path


def normalizar_nome(nome: str) -> str:
    """Padroniza o nome removendo acentos, pontuação e espaços extras."""
    if not nome:
        return ""
    nfkd = unicodedata.normalize("NFKD", nome.upper())
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return re.sub(r"[^A-Z0-9]", "", sem_acento)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=4)
        handle.write("\n")


def build_name_index(json_files: list[Path]) -> dict[str, str]:
    """
    Mapeia o nome completo e citações (listaNomesCitacao) de cada pesquisador
    diretamente para o seu ID Lattes de 16 dígitos.
    """
    name_to_id: dict[str, str] = {}

    for path in json_files:
        data = load_json(path)
        id_lattes = (data.get("_id") or "").strip()
        full_name = (data.get("nome_completo") or "").strip()
        if not id_lattes or not full_name:
            continue

        # Nome completo do pesquisador
        name_to_id[normalizar_nome(full_name)] = id_lattes

        # Todas as citações registradas/identificadas (listaNomesCitacao)
        for cit in data.get("listaNomesCitacao", []):
            if cit:
                name_to_id[normalizar_nome(cit)] = id_lattes

    return name_to_id


def fill_missing_ids(
    json_files: list[Path],
    name_to_id: dict[str, str],
    log_path: Path,
) -> dict:
    """Percorre os arquivos e preenche o id_lattes dos coautores e orientandos."""
    summary = {
        "files_processed": 0,
        "files_updated": 0,
        "filled_owner": 0,
        "filled_coauthors": 0,
        "filled_orientations": 0,
    }

    secoes_producoes = [
        "listaPB",
        "trabalhos_completos",
        "resumos_expandidos",
        "resumos_publicados",
        "producao_revistas",
    ]

    with log_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["json_file", "secao", "titulo", "colaborador", "id_lattes", "tipo"])

        for path in json_files:
            data = load_json(path)
            changed = False
            summary["files_processed"] += 1
            owner_id = (data.get("_id") or "").strip()

            # 1. Preenchimento nas produções
            for sec in secoes_producoes:
                for idx, item in enumerate(data.get(sec, []), start=1):
                    if not isinstance(item, dict):
                        continue
                    for colab in item.get("colaboradores", []):
                        current_id = (colab.get("id_lattes") or "").strip()
                        if current_id:
                            continue

                        nome_colab = (colab.get("nome") or "").strip()
                        if not nome_colab:
                            continue

                        chave = normalizar_nome(nome_colab)
                        if chave in name_to_id:
                            matched_id = name_to_id[chave]
                            colab["id_lattes"] = matched_id
                            changed = True

                            tipo = "proprio_pesquisador" if matched_id == owner_id else "coautor_rede"
                            if tipo == "proprio_pesquisador":
                                summary["filled_owner"] += 1
                            else:
                                summary["filled_coauthors"] += 1

                            writer.writerow([
                                path.name,
                                f"{sec}[{idx}]",
                                item.get("titulo", ""),
                                nome_colab,
                                matched_id,
                                tipo,
                            ])

            # 2. Preenchimento nas orientações
            for sec in ["orientacoes_concluidas", "orientacoes_em_andamento"]:
                for idx, item in enumerate(data.get(sec, []), start=1):
                    if not isinstance(item, dict):
                        continue
                    current_id = (item.get("id_lattes") or "").strip()
                    if current_id:
                        continue

                    aluno = (item.get("aluno") or "").strip()
                    if not aluno:
                        continue

                    chave = normalizar_nome(aluno)
                    if chave in name_to_id:
                        matched_id = name_to_id[chave]
                        item["id_lattes"] = matched_id
                        changed = True
                        summary["filled_orientations"] += 1
                        writer.writerow([
                            path.name,
                            f"{sec}[{idx}]",
                            item.get("titulo", ""),
                            aluno,
                            matched_id,
                            "aluno_orientacao",
                        ])

            if changed:
                write_json(path, data)
                summary["files_updated"] += 1

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preenche id_lattes de coautores e alunos com base no nome e citações da rede."
    )
    parser.add_argument(
        "--folder",
        default="curriculos_json",
        help="Caminho para a pasta com os JSONs (padrão: curriculos_json).",
    )
    parser.add_argument(
        "--log",
        default="filled_idlattes_log.csv",
        help="Caminho do arquivo de log CSV (padrão: filled_idlattes_log.csv).",
    )
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    json_files = sorted(folder.glob("*.json"))
    if not json_files:
        raise SystemExit(f"Nenhum arquivo JSON encontrado em {folder}")

    # Criação do mapa de busca via nome completo + listaNomesCitacao
    name_to_id = build_name_index(json_files)
    log_path = Path(args.log).expanduser().resolve()

    summary = fill_missing_ids(json_files, name_to_id, log_path)

    total_preenchidos = summary["filled_owner"] + summary["filled_coauthors"] + summary["filled_orientations"]

    print("=" * 70)
    print(" PREENCHIMENTO SIMPLES DE IDs LATTES CONCLUÍDO")
    print("=" * 70)
    print(f"Arquivos analisados: {summary['files_processed']}")
    print(f"Arquivos atualizados: {summary['files_updated']}")
    print(f"Total de IDs preenchidos: {total_preenchidos}")
    print(f"  - Próprio pesquisador na publicação: {summary['filled_owner']}")
    print(f"  - Coautores identificados na rede: {summary['filled_coauthors']}")
    print(f"  - Alunos/orientandos na rede: {summary['filled_orientations']}")
    print(f"Log salvo em: {log_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
