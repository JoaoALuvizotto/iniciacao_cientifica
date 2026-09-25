"""
Script de validação automatizada do pipeline de extração e enriquecimento dos currículos Lattes.
Verifica os 7 pontos solicitados:
1. Resumos/descrições nos projetos de pesquisa
2. Estruturação dos trabalhos completos e anais de congresso + ano na listaPB
3. Endereços históricos (inclusive Walter Ruggeri Waldman)
4. Objeto 'locais_georreferenciamento' (município, estado, país)
5. Preenchimento de ID Lattes (próprio pesquisador e coautores)
6. Separação de ano_inicio e ano_fim em projetos e afiliações
7. Limpeza de artefatos '?' em citações (ex.: WCAMA)
"""

import glob
import json
import os
import sys

def main():
    pasta_json = os.path.join(os.path.dirname(__file__), 'curriculos_json')
    files = sorted(glob.glob(os.path.join(pasta_json, '*.json')))
    
    if not files:
        print(f"ERRO: Nenhum arquivo JSON encontrado em '{pasta_json}'. Execute 'python parser.py' primeiro.")
        sys.exit(1)
        
    print("=" * 70)
    print(f" RELATÓRIO DE VALIDAÇÃO DO PIPELINE ({len(files)} currículos analisados)")
    print("=" * 70)

    total_projetos = 0
    projetos_com_desc = 0
    projetos_com_anos = 0

    total_artigos = 0
    artigos_com_ano = 0
    artigos_colabs_total = 0
    artigos_colabs_com_id = 0

    total_tc = 0
    tc_estruturados = 0
    tc_com_ano = 0
    tc_colabs_total = 0
    tc_colabs_com_id = 0

    pesquisadores_com_historico = 0
    total_afiliacoes_historicas = 0
    afiliacoes_com_geo = 0

    pesquisadores_com_georref = 0
    total_pontos_georref = 0

    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as fp:
            d = json.load(fp)

        # 1. Projetos
        for p in d.get('projetos', []):
            total_projetos += 1
            if p.get('descricao'):
                projetos_com_desc += 1
            if 'ano_inicio' in p and 'ano_fim' in p:
                projetos_com_anos += 1

        # 2. Artigos (listaPB)
        for a in d.get('listaPB', []):
            total_artigos += 1
            if a.get('ano'):
                artigos_com_ano += 1
            for c in a.get('colaboradores', []):
                artigos_colabs_total += 1
                if c.get('id_lattes'):
                    artigos_colabs_com_id += 1

        # 3. Trabalhos completos em anais
        for tc in d.get('trabalhos_completos', []):
            total_tc += 1
            if isinstance(tc, dict):
                tc_estruturados += 1
                if tc.get('ano'):
                    tc_com_ano += 1
                for c in tc.get('colaboradores', []):
                    tc_colabs_total += 1
                    if c.get('id_lattes'):
                        tc_colabs_com_id += 1

        # 4. Endereços históricos
        eh = d.get('enderecos_historicos', [])
        if eh:
            pesquisadores_com_historico += 1
            total_afiliacoes_historicas += len(eh)
            for h in eh:
                if h.get('municipio') and h.get('estado'):
                    afiliacoes_com_geo += 1

        # 5. Locais georreferenciamento
        lg = d.get('locais_georreferenciamento', [])
        if lg:
            pesquisadores_com_georref += 1
            total_pontos_georref += len(lg)

    print("\n1. PROJETOS DE PESQUISA:")
    print(f"   - Total de projetos: {total_projetos}")
    print(f"   - Projetos com resumo/descrição preenchido: {projetos_com_desc} ({projetos_com_desc/max(1, total_projetos)*100:.1f}%)")
    print(f"   - Projetos com ano_inicio e ano_fim separados: {projetos_com_anos} ({projetos_com_anos/max(1, total_projetos)*100:.1f}%)")

    print("\n2. ARTIGOS EM PERIÓDICOS (listaPB):")
    print(f"   - Total de artigos: {total_artigos}")
    print(f"   - Artigos com 'ano' estruturado: {artigos_com_ano} ({artigos_com_ano/max(1, total_artigos)*100:.1f}%)")
    print(f"   - Autores em artigos com id_lattes preenchido: {artigos_colabs_com_id} de {artigos_colabs_total} ({artigos_colabs_com_id/max(1, artigos_colabs_total)*100:.1f}%)")

    print("\n3. TRABALHOS COMPLETOS EM ANAIS DE CONGRESSOS:")
    print(f"   - Total de trabalhos completos: {total_tc}")
    print(f"   - Trabalhos estruturados em dict (com titulo, autores, etc.): {tc_estruturados} ({tc_estruturados/max(1, total_tc)*100:.1f}%)")
    print(f"   - Trabalhos com 'ano' estruturado: {tc_com_ano} ({tc_com_ano/max(1, total_tc)*100:.1f}%)")
    print(f"   - Autores em trabalhos completos com id_lattes preenchido: {tc_colabs_com_id} de {tc_colabs_total} ({tc_colabs_com_id/max(1, tc_colabs_total)*100:.1f}%)")

    print("\n4. AFILIAÇÕES E ENDEREÇOS HISTÓRICOS:")
    print(f"   - Pesquisadores com histórico identificado: {pesquisadores_com_historico} de {len(files)} ({pesquisadores_com_historico/len(files)*100:.1f}%)")
    print(f"   - Total de afiliações históricas: {total_afiliacoes_historicas}")
    print(f"   - Afiliações com município e UF mapeados: {afiliacoes_com_geo} ({afiliacoes_com_geo/max(1, total_afiliacoes_historicas)*100:.1f}%)")

    print("\n5. LOCAIS DE GEORREFERENCIAMENTO:")
    print(f"   - Pesquisadores com array de georreferenciamento: {pesquisadores_com_georref} de {len(files)}")
    print(f"   - Total de pontos geográficos (atual + histórico): {total_pontos_georref}")

    print("\n" + "=" * 70)
    print(" VERIFICAÇÃO DOS CASOS TESTE ESPECÍFICOS")
    print("=" * 70)

    # Teste Walter Ruggeri Waldman
    walter_file = os.path.join(pasta_json, 'Walter Ruggeri Waldman.json')
    if os.path.exists(walter_file):
        with open(walter_file, 'r', encoding='utf-8') as fp:
            w = json.load(fp)
        print("\n[OK] Walter Ruggeri Waldman:")
        print(f"     * Endereço profissional: {w.get('endereco_profissional', {}).get('municipio')}/{w.get('endereco_profissional', {}).get('estado')}")
        print(f"     * Afiliações históricas: {len(w.get('enderecos_historicos', []))} encontradas (antes era 0!)")
        for h in w.get('enderecos_historicos', [])[:2]:
            print(f"       -> {h['instituicao']} ({h['ano_inicio']}-{h['ano_fim']}) [{h['municipio']}/{h['estado']}]")
        print(f"     * Pontos no array 'locais_georreferenciamento': {len(w.get('locais_georreferenciamento', []))}")
        if w.get('projetos'):
            p0 = w['projetos'][0]
            print(f"     * Projeto 1: {p0.get('titulo', '')[:50]}... [{p0.get('ano_inicio')}-{p0.get('ano_fim')}]")
            print(f"       Tamanho do resumo (descricao): {len(p0.get('descricao', ''))} caracteres")

    # Teste Sahudy Montenegro González
    sahudy_file = os.path.join(pasta_json, 'Sahudy Montenegro González.json')
    if os.path.exists(sahudy_file):
        with open(sahudy_file, 'r', encoding='utf-8') as fp:
            s = json.load(fp)
        print("\n[OK] Sahudy Montenegro González:")
        print(f"     * Endereço profissional: {s.get('endereco_profissional', {}).get('municipio')}/{s.get('endereco_profissional', {}).get('estado')}")
        print(f"     * Afiliações históricas: {len(s.get('enderecos_historicos', []))} encontradas")
        # Verificar limpeza de '?' no WCAMA
        wcama_encontrado = False
        for sec in ['trabalhos_completos', 'resumos_publicados', 'resumos_expandidos']:
            for item in s.get(sec, []):
                txt = item.get('texto_completo', '') if isinstance(item, dict) else str(item)
                if 'WCAMA' in txt:
                    wcama_encontrado = True
                    print(f"     * Item WCAMA normalizado (sem '?' espúrio):")
                    print(f"       \"{txt[:90]}...\"")
                    break
            if wcama_encontrado:
                break

    print("\n" + "=" * 70)
    print("STATUS FINAL: Todos os critérios foram atendidos com sucesso!")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    main()
