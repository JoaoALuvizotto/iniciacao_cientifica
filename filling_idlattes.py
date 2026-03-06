"""
Preenchedor de IDs: preenche id_lattes ausentes em colaboradores de producoes
com base na lista de nomes de citacao presente nos JSONs.

Uso:
	python filling_idlattes.py --folder <pasta-jsons> [--log filled_idlattes_log.csv]

O script le todos os JSONs da pasta informada, tenta preencher id_lattes
quando existe correspondencia unica, e registra cada preenchimento em CSV.
"""

import argparse
import csv
import json
import re
from pathlib import Path

def normalizar_nome(nome: str) -> str:
    """
    Padroniza o nome para facilitar o cruzamento:
    - Converte para maiúsculas
    - Remove TODOS os espaços em branco
    """
    if not nome:
        return ""
    
    nome_padronizado = nome.upper()
    nome_padronizado = re.sub(r'\s+', '', nome_padronizado)
    
    return nome_padronizado


def load_json(path: Path) -> dict:
	with path.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def write_json(path: Path, data: dict) -> None:
	with path.open("w", encoding="utf-8") as handle:
		json.dump(data, handle, ensure_ascii=False, indent=2)
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
            ]
        )

        for path in json_files:
            data = load_json(path)
            changed = False
            summary["files_processed"] += 1

            # 1. Processar os coautores nos artigos (listaPB)
            for item_index, item in enumerate(data.get("listaPB", []), start=1):
                for collaborator in item.get("colaboradores", []):
                    current_id = (collaborator.get("id_lattes") or "").strip()
                    if current_id:
                        continue

                    summary["collaborators_missing"] += 1
                    key = (collaborator.get("nome", "") or "").strip()
                    if not key:
                        summary["no_match"] += 1
                        continue

                    # NORMALIZA antes de buscar no dicionário!
                    chave_busca = normalizar_nome(key)
                    ids = name_to_ids.get(chave_busca, set())
                    
                    if len(ids) == 1:
                        filled_id = next(iter(ids))
                        collaborator["id_lattes"] = filled_id
                        summary["filled"] += 1
                        changed = True
                        writer.writerow(
                            [
                                path.name,
                                f"listaPB[{item_index}]",
                                item.get("titulo", ""),
                                key,
                                filled_id,
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
                    current_id = (item.get("id_lattes") or "").strip()
                    if current_id:
                        continue

                    summary["collaborators_missing"] += 1
                    key = (item.get("aluno", "") or "").strip()
                    if not key:
                        summary["no_match"] += 1
                        continue

                    # NORMALIZA antes de buscar no dicionário!
                    chave_busca = normalizar_nome(key)
                    ids = name_to_ids.get(chave_busca, set())
                    
                    if len(ids) == 1:
                        filled_id = next(iter(ids))
                        item["id_lattes"] = filled_id # Injeta a chave no dicionário
                        summary["filled"] += 1
                        changed = True
                        writer.writerow(
                            [
                                path.name,
                                f"{section_name}[{item_index}]",
                                item.get("titulo", ""),
                                key,
                                filled_id,
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
		description="Fill missing collaborator id_lattes using listaNomesCitacao across JSON files."
	)
	parser.add_argument(
		"--folder",
		default="JSONs",
		help="Path to the folder containing JSON files (default: JSONs).",
	)
	parser.add_argument(
		"--log",
		default="filled_idlattes_log.csv",
		help="CSV path for logging filled IDs (default: filled_idlattes_log.csv).",
	)
	args = parser.parse_args()

	folder = Path(args.folder).expanduser().resolve()
	json_files = sorted(folder.glob("*.json"))
	if not json_files:
		raise SystemExit(f"No JSON files found in {folder}")

	name_to_ids = build_name_index(json_files)
	log_path = Path(args.log).expanduser().resolve()
	summary = fill_missing_ids(json_files, name_to_ids, log_path)

	print("Done.")
	print(
		"Processed: {files_processed} | Updated: {files_updated} | "
		"Missing: {collaborators_missing} | Filled: {filled} | "
		"Ambiguous: {ambiguous} | No match: {no_match}".format(**summary)
	)
	print(f"Log: {log_path}")


if __name__ == "__main__":
	main()
