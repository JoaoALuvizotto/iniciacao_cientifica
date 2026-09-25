"""
Preenchedor de IDs: preenche id_lattes ausentes em colaboradores de produções (listaPB, trabalhos_completos, etc.)
e alunos de orientações com base na lista de nomes de citação, nomes completos e variações dos pesquisadores nos JSONs.

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
    """
    Padroniza o nome para facilitar o cruzamento:
    - Decompõe caracteres acentuados (NFKD) e remove diacríticos
    - Converte para maiúsculas
    - Mantém apenas caracteres alfanuméricos A-Z e 0-9
    """
    if not nome:
        return ""
    nfkd = unicodedata.normalize('NFKD', nome.upper())
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return re.sub(r'[^A-Z0-9]', '', sem_acento)


def gerar_variacoes_citacao(nome_completo: str) -> list[str]:
    """
    Gera variações padrão de citação (ex: 'SILVA, J. S.', 'SILVA, JOAO S.') a partir do nome completo.
    Especialmente útil quando o pesquisador não preencheu o campo de citações no Lattes.
    """
    if not nome_completo:
        return []
    partes = nome_completo.strip().split()
    if len(partes) < 2:
        return [nome_completo]
    sobrenome = partes[-1]
    prenomes = partes[:-1]
    iniciais = [p[0] for p in prenomes]
    
    variacoes = [
        f"{sobrenome}, {' '.join(iniciais)}",
        f"{sobrenome}, {'. '.join(iniciais)}.",
        f"{sobrenome}, {' '.join(prenomes)}",
        f"{sobrenome}, {prenomes[0]} {' '.join(iniciais[1:])}".strip()
    ]
    return variacoes


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=4)
        handle.write("\n")


def build_name_index(json_files: list[Path]) -> dict[str, set[str]]:
    name_to_ids: dict[str, set[str]] = {}
    for path in json_files:
        data = load_json(path)
        id_lattes = (data.get("_id") or "").strip()
        full_name = (data.get("nome_completo") or "").strip()
        if full_name and id_lattes:
            chave_normalizada = normalizar_nome(full_name)
            name_to_ids.setdefault(chave_normalizada, set()).add(id_lattes)
            
            # Adiciona variações sintéticas de citação para permitir correspondência mesmo sem listaNomesCitacao explícita
            for var in gerar_variacoes_citacao(full_name):
                name_to_ids.setdefault(normalizar_nome(var), set()).add(id_lattes)
        
        for raw_name in data.get("listaNomesCitacao", []):
            key = (raw_name or "").strip()
            if not key or not id_lattes:
                continue

            chave_normalizada = normalizar_nome(key)
            name_to_ids.setdefault(chave_normalizada, set()).add(id_lattes)
    return name_to_ids


def fill_missing_ids(
    json_files: list[Path],
    name_to_ids: dict[str, set[str]],
    log_path: Path,
) -> dict:
    summary = {
        "files_processed": 0,
        "collaborators_missing": 0,
        "filled": 0,
        "filled_owner": 0,
        "filled_coauthors": 0,
        "ambiguous": 0,
        "no_match": 0,
        "files_updated": 0,
    }
    
    with log_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "json_file",
                "section",
                "title",
                "collaborator_name",
                "filled_id_lattes",
                "tipo_resolucao",
            ]
        )

        for path in json_files:
            data = load_json(path)
            changed = False
            summary["files_processed"] += 1

            owner_id = (data.get("_id") or "").strip()
            owner_name = (data.get("nome_completo") or "").strip()
            owner_variations = set()
            if owner_name:
                owner_variations.add(normalizar_nome(owner_name))
                for v in gerar_variacoes_citacao(owner_name):
                    owner_variations.add(normalizar_nome(v))
            for n in data.get("listaNomesCitacao", []):
                owner_variations.add(normalizar_nome(n))

            # 1. Processar seções de produções com colaboradores (listaPB, trabalhos_completos, etc.)
            secoes_producoes = [
                "listaPB",
                "trabalhos_completos",
                "resumos_expandidos",
                "resumos_publicados"
            ]

            for sec in secoes_producoes:
                for item_index, item in enumerate(data.get(sec, []), start=1):
                    if not isinstance(item, dict):
                        continue
                    for collaborator in item.get("colaboradores", []):
                        current_id = (collaborator.get("id_lattes") or "").strip()
                        if current_id:
                            continue

                        summary["collaborators_missing"] += 1
                        key = (collaborator.get("nome", "") or "").strip()
                        if not key:
                            summary["no_match"] += 1
                            continue

                        chave_busca = normalizar_nome(key)

                        # Prioridade 1: É o próprio autor do currículo
                        if owner_id and chave_busca in owner_variations:
                            collaborator["id_lattes"] = owner_id
                            summary["filled"] += 1
                            summary["filled_owner"] += 1
                            changed = True
                            writer.writerow(
                                [
                                    path.name,
                                    f"{sec}[{item_index}]",
                                    item.get("titulo", ""),
                                    key,
                                    owner_id,
                                    "proprio_pesquisador",
                                ]
                            )
                        else:
                            # Prioridade 2: É um coautor registrado no catálogo de pesquisadores
                            ids = name_to_ids.get(chave_busca, set())
                            if len(ids) == 1:
                                filled_id = next(iter(ids))
                                collaborator["id_lattes"] = filled_id
                                summary["filled"] += 1
                                summary["filled_coauthors"] += 1
                                changed = True
                                writer.writerow(
                                    [
                                        path.name,
                                        f"{sec}[{item_index}]",
                                        item.get("titulo", ""),
                                        key,
                                        filled_id,
                                        "coautor_reconhecido",
                                    ]
                                )
                            elif len(ids) > 1:
                                summary["ambiguous"] += 1
                            else:
                                summary["no_match"] += 1

            # 2. Processar os alunos nas orientações
            secoes_de_orientacao = ["orientacoes_concluidas", "orientacoes_em_andamento"]
            for section_name in secoes_de_orientacao:
                for item_index, item in enumerate(data.get(section_name, []), start=1):
                    if not isinstance(item, dict):
                        continue
                    current_id = (item.get("id_lattes") or "").strip()
                    if current_id:
                        continue

                    summary["collaborators_missing"] += 1
                    key = (item.get("aluno", "") or "").strip()
                    if not key:
                        summary["no_match"] += 1
                        continue

                    chave_busca = normalizar_nome(key)
                    ids = name_to_ids.get(chave_busca, set())
                    
                    if len(ids) == 1:
                        filled_id = next(iter(ids))
                        item["id_lattes"] = filled_id
                        summary["filled"] += 1
                        summary["filled_coauthors"] += 1
                        changed = True
                        writer.writerow(
                            [
                                path.name,
                                f"{section_name}[{item_index}]",
                                item.get("titulo", ""),
                                key,
                                filled_id,
                                "aluno_orientacao",
                            ]
                        )
                    elif len(ids) > 1:
                        summary["ambiguous"] += 1
                    else:
                        summary["no_match"] += 1

            if changed:
                write_json(path, data)
                summary["files_updated"] += 1

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preenche id_lattes ausentes em colaboradores e orientações nos JSONs."
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

    name_to_ids = build_name_index(json_files)
    log_path = Path(args.log).expanduser().resolve()
    summary = fill_missing_ids(json_files, name_to_ids, log_path)

    print("Concluído.")
    print(
        "Processados: {files_processed} | Atualizados: {files_updated} | "
        "Faltando: {collaborators_missing} | Preenchidos: {filled} "
        "(Próprio pesquisador: {filled_owner}, Coautores: {filled_coauthors}) | "
        "Ambíguos: {ambiguous} | Sem correspondência: {no_match}".format(**summary)
    )
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()
