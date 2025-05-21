import filters_paths

def example_usage(tree_data):
    """
    Exemplo de como usar as funções de filtragem com diferentes tipos de expressões.
    
    Esta função demonstra várias formas de filtrar dados usando expressões condicionais,
    mostrando os resultados de cada filtro de forma detalhada.
    
    Args:
        tree_data: Dados da árvore no formato JSON para filtrar
    """
    # Função auxiliar para mostrar resultados de maneira consistente
    def print_results(description, results, is_return_paths=False):
        print("\n" + "="*80)
        print(f"{description} (Encontrados: {len(results)})")
        print("-"*80)
        
        if not results:
            print("Nenhum resultado encontrado.")
            return
            
        if is_return_paths or isinstance(results, dict):
            # For return_paths format (dictionary of paths to values)
            for path, values in results.items():
                print(f"Path: {path}")
                print(f"Values ({len(values)}):")
                for i, value in enumerate(values):
                    print(f"  {i+1}. {value}")
                print()
        else:
            # For regular format (list of records)    
            for i, result in enumerate(results):
                print(f"Resultado #{i+1}:")
                print(f"  ID: {result.get('id', 'N/A')}")
                
                # Mostrar campos relevantes
                if 'fields' in result and result['fields'] is not None:
                    print("  Campos:")
                    for field in result['fields']:
                        path = field.get('path', 'N/A')
                        value = field.get('value', 'N/A')
                        field_type = field.get('type', 'N/A')
                        print(f"    {path}: {value} ({field_type})")
                else:
                    print("  Campos: Nenhum campo encontrado")
                
                # Mostrar se existem dados aninhados
                if 'data' in result and result['data'] is not None and len(result['data']) > 0:
                    print(f"  Contém {len(result['data'])} nós de dados aninhados")
                
                # Mostrar data de criação, se disponível
                if 'creation' in result and result['creation'] is not None:
                    print(f"  Data de criação: {result['creation']}")
                
                print()  # Linha em branco entre resultados

    # # Função auxiliar para demonstrar o uso direto das funções de pesquisa
    # def test_direct_functions(path):
    #     print("\n" + "="*80)
    #     print(f"VALORES PARA O CAMINHO: {path}")
    #     print("-"*80)
        
    #     # Obter primeiro valor
    #     first_value = get_first_value(tree_data, path)
    #     print(f"first({path}) = {first_value}")
        
    #     # Obter último valor
    #     last_value = get_last_value(tree_data, path)
    #     print(f"last({path}) = {last_value}")
        
    #     # Obter valor da data de criação mais recente
    #     firstc_value = get_first_value_date(tree_data, path)
    #     print(f"firstc({path}) = {firstc_value}")
        
    #     # Obter valor da data de criação mais antiga
    #     lastc_value = get_last_value_date(tree_data, path)
    #     print(f"lastc({path}) = {lastc_value}")
        
    #     print()  # Linha em branco

    # Filtro simples
    print("\n1. FILTRO SIMPLES")
    filter_expr = "True"
    record_id = "0196c4d0-b7ad-7b23-ad96-b316ce979d6f"
    results = filters_paths.filter_tree_data(tree_data, filter_expr, return_paths=["e00019v"], record_id = record_id)
    print_results(f"Itens onde {filter_expr}", results)

    # # Filtro com função contains
    # print("\n8. FILTRO COM FUNÇÃO CONTAINS")
    # filter_expr = "contains(e00009v, ' do ')"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)

    # # Filtro com função especial
    # print("\n2. PRIMEIRO VALOR")
    # filter_expr = "first(e00009v)"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)
    
    # # Filtro com função last
    # print("\n3. ÚLTIMO VALOR")
    # filter_expr = "last(e00009v)"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)
    
    # # Filtro com função firstc
    # print("\n4. PRIMEIRO VALOR POR DATA DE CRIAÇÃO (MAIS RECENTE)")
    # filter_expr = "firstc(e00009v)"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)
    
    # # Filtro com função lastc
    # print("\n5. ÚLTIMO VALOR POR DATA DE CRIAÇÃO (MAIS ANTIGA)")
    # filter_expr = "lastc(e00009v)"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)

    # # Filtro com operador lógico
    # print("\n3. FILTRO COM OPERADOR CONTEM")
    # filter_expr = "contains(e00001v,'mov')"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)

    # # Filtro com operador lógico
    # print("\n4. FILTRO COM OPERADOR MAIOR QUE")
    # filter_expr = "e00004v > 1"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)


    # # Filtro com operador lógico
    # print("\n5. FILTRO COM OPERADOR MAIOR LOGICO")
    # filter_expr = "contains(e00001v,'mov') and e00004v > 1"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)


    # # Filtro complexo
    # print("\n6. FILTRO COM OPERADOR COMPLEXO")
    # filter_expr = "contains(e00001v,'mov') and (e00004v == 1 or e00004v == 4)"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)

    # # Teste da função firstc isoladamente
    # print("\n13. FILTRO USANDO APENAS FIRSTC()")
    # filter_expr = "firstc(e00001v)"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr} não é null", results)
    
    # # Teste da função lastc isoladamente
    # print("\n14. FILTRO USANDO APENAS LASTC()")
    # filter_expr = "lastc(e00001v)"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr} não é null", results)

    # # Filtro com operador lógico
    # print("\n3. FILTRO COM OPERADOR MENOR QUE")
    # filter_expr = "e00004v < 2"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)    

    # # Filtro com operador lógico
    # print("\n3. FILTRO COM OPERADOR MENOR IGUAL QUE")
    # filter_expr = "e00004v <= 2"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)        

    # # Filtro com operador lógico
    # print("\n3. FILTRO COM OPERADOR MAIOR IGUAL QUE")
    # filter_expr = "e00004v >= 2"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)        


    # # Filtro com caminho específico e ID de registro
    # print("\n9. FILTRO COM CAMINHO ESPECÍFICO E ID DE REGISTRO")
    # filter_expr = "e00001v == 'Automovel'"
    # path_expr = "data"
    # record_id = "01967343-b7d4-7e20-908c-c48e8cf68789"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr, record_id=record_id, path_expr=path_expr)
    # print_results(f"Itens no caminho '{path_expr}' com ID '{record_id}' onde {filter_expr}", results)
    
    # # Teste com ID de registro mas sem caminho específico (caminho interno)
    # print("\n10. FILTRO COM ID DE REGISTRO SEM CAMINHO ESPECÍFICO")
    # filter_expr = "e00004v == 2"
    # record_id = "0196778f-92d5-71e2-aea3-e2fbf6faffdc"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr, record_id=record_id)
    # print_results(f"Itens com ID '{record_id}' onde {filter_expr} (caminho interno)", results)
    
    # # Teste com ID de registro e caminho não interno (formato de índice)
    # print("\n11. FILTRO COM ID DE REGISTRO E CAMINHO NÃO INTERNO (FORMATO DE ÍNDICE)")
    # filter_expr = "e00001v == 'Automovel'"
    # path_expr = "data[0][0]"  # Caminho começando com índice (deve ignorar o record_id)
    # record_id = "0196778f-92d5-71e2-aea3-e2fbf6faffdc"  # ID que não está relacionado ao "Automovel"
    # results = filters_paths.filter_tree_data(tree_data, filter_expr, record_id=record_id, path_expr=path_expr)
    # print_results(f"Itens no caminho '{path_expr}' com ID '{record_id}' onde {filter_expr} (caminho não interno)", results)
    
    # # Teste para confirmar que o caminho de índice ignora o record_id
    # print("\n12. VERIFICAÇÃO DE QUE O CAMINHO DE ÍNDICE IGNORA O RECORD_ID")
    # filter_expr = "e00001v == 'Automovel'"
    # path_expr_without_index = "data"  # Sem índice - deve considerar o record_id
    # record_id = "01967343-b7d4-7e20-908c-c48e8cf68789"  # ID do Automovel
    # results_with_id = filters_paths.filter_tree_data(tree_data, filter_expr, record_id=record_id, path_expr=path_expr_without_index)
    
    # path_expr_with_index = "data[0]"  # Com índice - deve ignorar o record_id
    # results_without_id = filters_paths.filter_tree_data(tree_data, filter_expr, record_id=record_id, path_expr=path_expr_with_index)
    
    # print(f"A. Resultados com caminho sem índice '{path_expr_without_index}' (deve considerar record_id): {len(results_with_id)}")
    # print_results(f"Detalhes dos resultados para caminho sem índice '{path_expr_without_index}':", results_with_id)
    
    # print(f"B. Resultados com caminho com índice '{path_expr_with_index}' (deve ignorar record_id): {len(results_without_id)}")
    # print_results(f"Detalhes dos resultados para caminho com índice '{path_expr_with_index}':", results_without_id)
    
    # # Teste com caminho que inclui um ponto (deve ser tratado como interno ao registro)
    # path_expr_with_dot = "data.records"  # Caminho com ponto
    # results_with_dot = filters_paths.filter_tree_data(tree_data, filter_expr, record_id, path_expr_with_dot)
    # print(f"C. Resultados com caminho com ponto '{path_expr_with_dot}' (deve considerar record_id): {len(results_with_dot)}")
    
    # print(f"Comportamento esperado: A deve retornar resultados específicos do registro, B deve ignorar o record_id e buscar em toda a árvore, C deve considerar o record_id como A")


    # # Filtro complexo
    # print("\n4. FILTRO COMPLEXO")
    # filter_expr = "e00001v == 'Automovel' and (contains(e00002v, 'Test') or firstc(e00003v) == 'Value')"
    # results = filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)

    # # Mostrar quais são os valores de e00050v para referência
    # print("\n5. REFERÊNCIA: VALORES DE e00050v")
    # path_expr = "data[2].data[0].data[1].data"
    # all_items = jmespath.search(path_expr, tree_data) or []
    # print(f"Todos os valores de e00050v no caminho especificado:")
    # for item in all_items:
    #     if 'fields' in item and item['fields'] is not None:
    #         for field in item['fields']:
    #             if field.get('path') == 'e00050v':
    #                 print(f"  ID: {item.get('id', 'N/A')}, Valor: {field.get('value')}")

    # # Filtro com caminho específico e ID de registro
    # print("\n6. FILTRO COM CAMINHO ESPECÍFICO E ID DE REGISTRO")
    # filter_expr = "e00050v >= 100"
    # path_expr = "data[2].data[0].data[1].data"
    # record_id = "0196b01a-2163-7cb2-93b9-c8b1342e3a4e"
    # results = filter_tree_data(tree_data, filter_expr, path_expr, record_id)
    # print_results(f"Itens no caminho '{path_expr}' com ID '{record_id}' onde {filter_expr}", results)

    # # Filtro alternativo para valores numéricos (maior que 10)
    # print("\n7. FILTRO PARA VALORES NUMÉRICOS")
    # filter_expr = "e00050v >= 10"
    # path_expr = "data[2].data[0].data[1].data"
    # results = filter_tree_data(tree_data, filter_expr, path_expr)
    # print_results(f"Itens no caminho '{path_expr}' onde {filter_expr}", results)

    # # Filtro com função contains
    # print("\n8. FILTRO COM FUNÇÃO CONTAINS")
    # filter_expr = "contains(e00001v, 'Equip')"
    # results = filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr}", results)

    # # NOVOS TESTES: Uso isolado das funções especiais
    
    # # Teste da função first isoladamente
    # print("\n11. FILTRO USANDO APENAS FIRST()")
    # filter_expr = "first(e00001v)"
    # results = filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr} não é null", results)
    
    # # Teste da função last isoladamente
    # print("\n12. FILTRO USANDO APENAS LAST()")
    # filter_expr = "last(e00001v)"
    # results = filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr} não é null", results)
    
    # # Teste da função firstc isoladamente
    # print("\n13. FILTRO USANDO APENAS FIRSTC()")
    # filter_expr = "firstc(e00001v)"
    # results = filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr} não é null", results)
    
    # # Teste da função lastc isoladamente
    # print("\n14. FILTRO USANDO APENAS LASTC()")
    # filter_expr = "lastc(e00001v)"
    # results = filter_tree_data(tree_data, filter_expr)
    # print_results(f"Itens onde {filter_expr} não é null", results)
    
    # # TESTES DIRETOS DAS FUNÇÕES DE PESQUISA
    # print("\n15. TESTE DIRETO DAS FUNÇÕES DE PESQUISA")
    # # Testar com diferentes campos
    # test_direct_functions("e00001v")  # Campo de tipo string
    # test_direct_functions("e00050v")  # Campo de tipo numérico
    # test_direct_functions("e00027v")  # Campo de tipo booleano
    # test_direct_functions("e00013v")  # Campo de tipo data
    
    # # Teste das funções com ID de registro específico
    # print("\n16. TESTE DAS FUNÇÕES FIRST/LAST COM ID DE REGISTRO ESPECÍFICO")
    # record_id = "01967343-b7d4-7e20-908c-c48e8cf68789"  # ID de um registro Automovel
    # print(f"Usando record_id: {record_id}")
    # print(f"first(e00001v) com record_id = {get_first_value(tree_data, 'e00001v', record_id=record_id)}")
    # print(f"last(e00001v) com record_id = {get_last_value(tree_data, 'e00001v', record_id=record_id)}")
    
    # # Demonstração do funcionamento da conversão do AST para filtros utilizáveis
    # print("\n17. DEMONSTRAÇÃO DO PARSER E CONVERSOR DE EXPRESSÕES")
    # converter = JMESPathExpressionConverter()
    # test_expressions = [
    #     "e00001v == 'Automovel'",
    #     "e00050v >= 100",
    #     "first(e00001v) == 'Automovel'",
    #     "contains(e00001v, 'Equip')",
    #     "e00001v == 'Automovel' and e00002v != True",
    #     "lastc(e00001v) == 'Caminhão Express'"
    # ]
    
    # for expr in test_expressions:
    #     print(f"\nExpressão: {expr}")
    #     ast = converter.parse(expr)
    #     print(f"AST: {ast}")
    #     # Criar uma representação da função de filtro
    #     filter_func = converter.convert_to_python_function(expr)
    #     print(f"Converter para função de filtro: Sucesso")

# def test_complex_queries(tree_data):
#     """
#     Testa consultas complexas com várias condições usando operadores AND e OR.
#     """
#     # Função auxiliar para mostrar resultados de maneira consistente
#     def print_results(description, results, is_return_paths=False):
#         print("\n" + "="*80)
#         print(f"{description} (Encontrados: {len(results)})")
#         print("-"*80)
        
#         if not results:
#             print("Nenhum resultado encontrado.")
#             return
            
#         if is_return_paths or isinstance(results, dict):
#             # For return_paths format (dictionary of paths to values)
#             for path, values in results.items():
#                 print(f"Path: {path}")
#                 print(f"Values ({len(values)}):")
#                 for i, value in enumerate(values):
#                     print(f"  {i+1}. {value}")
#                 print()
#         else:
#             # For regular format (list of records)
#             for i, result in enumerate(results):
#                 print(f"Resultado #{i+1}:")
#                 print(f"  ID: {result.get('id', 'N/A')}")
                
#                 # Mostrar campos relevantes
#                 if 'fields' in result and result['fields'] is not None:
#                     print("  Campos:")
#                     for field in result['fields']:
#                         path = field.get('path', 'N/A')
#                         value = field.get('value', 'N/A')
#                         field_type = field.get('type', 'N/A')
#                         print(f"    {path}: {value} ({field_type})")
#                 else:
#                     print("  Campos: Nenhum campo encontrado")
                
#                 # Mostrar se existem dados aninhados
#                 if 'data' in result and result['data'] is not None and len(result['data']) > 0:
#                     print(f"  Contém {len(result['data'])} nós de dados aninhados")
                
#                 # Mostrar data de criação, se disponível
#                 if 'creation' in result and result['creation'] is not None:
#                     print(f"  Data de criação: {result['creation']}")
                
#                 print()  # Linha em branco entre resultados

#     # Teste 1: Equipamentos móveis (sem restrição de região)
#     print("\nTESTE 1: Equipamentos e ferramentas móveis")
#     filter_expr = "contains(e00001v, 'moveis')"
#     results = filters_paths.filter_tree_data(tree_data, filter_expr)
#     print_results(f"Itens onde {filter_expr}", results)

#     # Teste 2: Automoveis ou Caminhões
#     print("\nTESTE 2: Automoveis ou Caminhões")
#     filter_expr = "e00001v == 'Automovel' or contains(e00001v, 'Caminhão')"
#     results = filters_paths.filter_tree_data(tree_data, filter_expr)
#     print_results(f"Itens onde {filter_expr}", results)

#     # Teste 3: Item específico com ID conhecido que tem quantidade = 2
#     print("\nTESTE 3: Item específico com quantidade = 2")
#     filter_expr = "e00004v == 2"
#     # Vamos especificar o ID do registro que sabemos que tem e00004v = 2
#     record_id = "0196778f-92d5-71e2-aea3-e2fbf6faffdc"
#     results = filters_paths.filter_tree_data(tree_data, filter_expr, record_id)
#     print_results(f"Itens com ID '{record_id}' onde {filter_expr}", results)

#     # Teste 4: Critério usando um operador de comparação com valor que sabemos existir
#     print("\nTESTE 4: Item com valor numérico válido para comparação")
#     filter_expr = "e00088v > 700000 or e00019v > 1000000"
#     results = filters_paths.filter_tree_data(tree_data, filter_expr)
#     print_results(f"Itens onde {filter_expr} (valor de contrato)", results)
    
#     # Teste 5: Combinação complexa com OR e AND
#     print("\nTESTE 5: Combinação complexa (caminhões OU equipamentos móveis com quantidade > 1)")
#     filter_expr = "contains(e00001v, 'Caminhão') or (contains(e00001v, 'moveis') and e00004v > 1)"
#     results = filters_paths.filter_tree_data(tree_data, filter_expr)
#     print_results(f"Itens onde {filter_expr}", results)
    
#     # Teste 6: Teste com datas
#     print("\nTESTE 6: Itens criados após 1º de maio de 2025")
#     filter_expr = "firstc(e00001v) and contains(e00009v, 'São') or contains(e00001v, 'Perfuratriz')"
#     results = filters_paths.filter_tree_data(tree_data, filter_expr)
#     print_results(f"Itens onde {filter_expr}", results)

# def test_return_paths_feature(tree_data):
#     """
#     Tests the new return_paths parameter functionality that extracts specific field values.
#     This test demonstrates how to use the return_paths parameter to extract values
#     for specific paths from the filtered records instead of returning the full records.
#     """
#     # Helper function to display results in a consistent format
#     def print_results(description, results, is_return_paths=False):
#         print("\n" + "="*80)
#         print(f"{description}")
#         print("-"*80)
        
#         if is_return_paths:
#             # For return_paths format (dictionary of paths to values)
#             if not results:
#                 print("No results found.")
#                 return
                
#             for path, values in results.items():
#                 print(f"Path: {path}")
#                 print(f"Values ({len(values)}):")
#                 for i, value in enumerate(values):
#                     print(f"  {i+1}. {value}")
#                 print()
#         else:
#             # For regular format (list of records)
#             if not results:
#                 print("No results found.")
#                 return
                
#             for i, result in enumerate(results):
#                 print(f"Result #{i+1}:")
#                 print(f"  ID: {result.get('id', 'N/A')}")
                
#                 if 'fields' in result and result['fields'] is not None:
#                     print("  Fields:")
#                     for field in result['fields']:
#                         path = field.get('path', 'N/A')
#                         value = field.get('value', 'N/A')
#                         field_type = field.get('type', 'N/A')
#                         print(f"    {path}: {value} ({field_type})")
#                 else:
#                     print("  Fields: None found")
                
#                 if 'data' in result and result['data'] is not None and len(result['data']) > 0:
#                     print(f"  Contains {len(result['data'])} nested data nodes")
                
#                 if 'creation' in result and result['creation'] is not None:
#                     print(f"  Creation date: {result['creation']}")
                
#                 print()  # Blank line between results

#     # Test 1: Extract single path value
#     print("\nTEST 1: Extract values for a single path")
#     filter_expr = "e00001v == 'Automovel'"
#     paths_to_extract = ["e00001v"]
    
#     # First, get the regular filtered records to compare
#     regular_results = filters_paths.filter_tree_data(tree_data, filter_expr)
#     print_results(f"Regular filtered records where {filter_expr}", regular_results)
    
#     # Then get the extracted values using return_paths
#     path_results = filters_paths.filter_tree_data(tree_data, filter_expr, return_paths=paths_to_extract)
#     print_results(f"Extracted values for {paths_to_extract} where {filter_expr}", path_results, True)
    
#     # Test 2: Extract multiple path values
#     print("\nTEST 2: Extract values for multiple paths")
#     filter_expr = "e00001v == 'Automovel' or contains(e00001v, 'Caminhão')"
#     paths_to_extract = ["e00001v", "e00009v", "e00004v"]
    
#     path_results = filters_paths.filter_tree_data(tree_data, filter_expr, return_paths=paths_to_extract)
#     print_results(f"Extracted values for {paths_to_extract} where {filter_expr}", path_results, True)
    
#     # Test 3: Extract values with record_id parameter
#     print("\nTEST 3: Extract values with record_id parameter")
#     filter_expr = "e00004v == 2"
#     record_id = "0196778f-92d5-71e2-aea3-e2fbf6faffdc"
#     paths_to_extract = ["e00004v", "e00001v"]
    
#     path_results = filters_paths.filter_tree_data(tree_data, filter_expr, return_paths=paths_to_extract, record_id=record_id)
#     print_results(f"Extracted values for {paths_to_extract} with record_id '{record_id}' where {filter_expr}", path_results, True)
    
#     # Test 4: Extract values using special functions (first, last, etc.)
#     print("\nTEST 4: Extract values using special functions")
#     filter_expr = "contains(e00001v, 'moveis')"
#     paths_to_extract = ["first(e00001v)", "last(e00009v)", "firstc(e00004v)"]
    
#     path_results = filters_paths.filter_tree_data(tree_data, filter_expr, return_paths=paths_to_extract)
#     print_results(f"Extracted values for special functions {paths_to_extract} where {filter_expr}", path_results, True)
    
#     # Test 5: Combine with path_expr parameter
#     print("\nTEST 5: Extract values with path_expr parameter")
#     filter_expr = "e00001v == 'Automovel'"
#     path_expr = "data"
#     paths_to_extract = ["e00001v", "e00009v"]
    
#     path_results = filters_paths.filter_tree_data(tree_data, filter_expr, return_paths=paths_to_extract, path_expr=path_expr)
#     print_results(f"Extracted values for {paths_to_extract} with path_expr '{path_expr}' where {filter_expr}", path_results, True)

if __name__ == "__main__":
    # Load example data
    import json
    with open('tree_data.json', 'r') as f:
        tree_data = json.load(f)
    
    # Run original tests
    example_usage(tree_data)
    
    # # Run tests with complex queries
    # test_complex_queries(tree_data)
    
    # # Run tests for the return_paths feature
    # test_return_paths_feature(tree_data)