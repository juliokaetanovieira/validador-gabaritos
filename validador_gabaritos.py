import os
from datetime import datetime
import pandas as pd
import unicodedata
import re

class ValidadorProdutos:
    def __init__(self, arquivo, log_callback=None):
        """
        Validador específico para planilha de produtos com 30 colunas
        Agora suporta Excel (.xlsx, .xls) e CSV
        """
        self.arquivo = arquivo
        self.df = None
        self.erros = []
        self.avisos = []
        self.logs = []  # Lista para armazenar os logs
        self.log_callback = log_callback  # Função de log
        
        # Definição das colunas esperadas
        self.colunas_esperadas = [
            'pIndice', 'pCodigo', 'pFornecedor', 'pReferencia', 'pCodigoBarras', 'pDescricao',
            'pDescricaoReduzida', 'pTamanho', 'pColecao', 'pLinha', 'pSegmento',
            'pGrupo', 'pFamilia', 'pSubFamilia', 'pNCM', 'pOrigem CST', 'pUN',
            'pMúltiplo', 'pM²/Pallet', 'pQUANTIDADE NA EMBALAGEM', 'pPeso',
            'pCusto', 'pPercST', 'pPercIPI', 'pPreçoVenda',
            'pExige Conferencia', 'pMarkup', 'pFrete', 'pCodigoSA',
            'pDesconto', 'pEmpresa'
        ]
        
        # Colunas obrigatórias
        self.colunas_obrigatorias = self.colunas_esperadas
    
    def log(self, message):
        """Função para armazenar as mensagens de log"""
        self.logs.append(message)
        if self.log_callback:
            self.log_callback(message)

    def carregar_arquivo(self):
        """Carrega o arquivo (Excel ou CSV) com tratamento robusto"""
        try:
            self.log(f"📂 Tentando carregar arquivo {self.arquivo}...")
            if not os.path.exists(self.arquivo):
                self.log(f"❌ Arquivo não encontrado: {self.arquivo}")
                return False
                
            _, ext = os.path.splitext(self.arquivo)
            ext = ext.lower()
            
            if ext in ['.xlsx', '.xls']:
                try:
                    engine = 'openpyxl' if ext == '.xlsx' else 'xlrd'
                    self.df = pd.read_excel(self.arquivo, engine=engine)
                    self.log(f"✅ Arquivo Excel carregado com sucesso usando engine {engine}")
                except Exception as e:
                    self.log(f"❌ Falha ao ler arquivo Excel: {e}")
                    return False
                    
            elif ext == '.csv':
                encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
                separadores = [';', ',', '\t']
                
                for encoding in encodings:
                    for sep in separadores:
                        try:
                            self.df = pd.read_csv(self.arquivo, sep=sep, encoding=encoding)
                            self.log(f"✅ CSV carregado com sucesso - Separador: '{sep}', Encoding: {encoding}")
                            break
                        except:
                            continue
                    if self.df is not None:
                        break
                
                if self.df is None:
                    self.log("❌ Falha ao ler arquivo CSV - Tentou todos os encodings e separadores")
                    return False
            else:
                self.log(f"❌ Formato de arquivo não suportado: {ext}")
                return False

            # NOVO: Renomear colunas "Unnamed" para "pIndice"
            if self.df is not None:
                colunas_renomeadas = []
                for i, coluna in enumerate(self.df.columns):
                    if 'Unnamed' in str(coluna):
                        novo_nome = 'pIndice'
                        self.df.rename(columns={coluna: novo_nome}, inplace=True)
                        colunas_renomeadas.append(f"'{coluna}' -> '{novo_nome}'")
                
                if colunas_renomeadas:
                    if len(colunas_renomeadas) == 1:
                        self.log(f"🔄 Coluna renomeada: {colunas_renomeadas[0]}")
                    else:
                        self.log(f"🔄 {len(colunas_renomeadas)} colunas Unnamed renomeadas para pIndice")

            self.log(f"📊 Total de linhas: {len(self.df)}")
            self.log(f"📋 Colunas encontradas: {list(self.df.columns)}")
            return True
            
        except Exception as e:
            self.log(f"❌ Erro ao carregar arquivo: {e}")
            return False

    def verificar_estrutura_colunas(self):
        """Verifica a estrutura das colunas"""
        self.log("\n🔍 Verificando estrutura das colunas...")
        
        # Normaliza as colunas do arquivo e as colunas esperadas
        colunas_arquivo = [self.remover_acentos_e_caracteres_especiais(coluna) for coluna in self.df.columns]
        colunas_esperadas_normalizadas = [self.remover_acentos_e_caracteres_especiais(coluna) for coluna in self.colunas_esperadas]
        
        # Comparando as colunas com acentos removidos e caracteres especiais
        colunas_faltando = [coluna for coluna in self.colunas_esperadas if self.remover_acentos_e_caracteres_especiais(coluna) not in colunas_arquivo]
        colunas_extras = [coluna for coluna in colunas_arquivo if coluna not in colunas_esperadas_normalizadas]
        
        if colunas_faltando:
            for coluna in colunas_faltando:
                erro = f"Coluna obrigatória '{coluna}' não encontrada no arquivo"
                self.erros.append(erro)
                self.log(f"❌ {erro}")
        
        if colunas_extras:
            for coluna in colunas_extras:
                aviso = f"Coluna extra '{coluna}' encontrada (será ignorada)"
                self.avisos.append(aviso)
                self.log(f"⚠️  {aviso}")
        
        if not colunas_faltando and not colunas_extras:
            self.log("✅ Estrutura de colunas está correta")
        
        return len(colunas_faltando) == 0
    
    def validar_colunas_obrigatorias(self):
        """Valida as colunas obrigatórias (não podem estar vazias)"""
        self.log("\n📋 Validando colunas obrigatórias...")
        for coluna in self.colunas_obrigatorias:
            if coluna not in self.df.columns:
                continue
            linhas_vazias = []
            for idx, valor in enumerate(self.df[coluna]):
                if pd.isna(valor) or str(valor).strip() == '':
                    linhas_vazias.append(idx + 2)
            if linhas_vazias:
                erro = f"❌ {coluna}: {len(linhas_vazias)} células vazias (linhas: {linhas_vazias[:10]}{'...' if len(linhas_vazias) > 10 else ''})"
                self.erros.append(erro)
                self.log(f"❌ {erro}")
            else:
                self.log(f"✅ {coluna}: Todas as células preenchidas")
    
    def aplicar_valores_padrao(self):
        """Verifica e aplica valores padrão para campos específicos"""
        self.log("\n🔧 Verificando campos que podem usar valores padrão...")
        
        campos_padrao = {
            'pCodigoBarras': 'SEM GTIN',
            'pTamanho': -1,
            'pColecao': -1,  # Observação: Já tratado no carregamento
            'pLinha': -1,
            'pSegmento': -1,
            'pGrupo': -1,
            'pFamilia': -1,
            'pSubFamilia': -1,
            'pNCM': '11111111',
            'pUN': 'UN',
            'pMúltiplo': 1,
            'pM²/Pallet': 0,
            'pQUANTIDADE NA EMBALAGEM': -1,
            'pPeso': -1,
            'pCusto': -1,
            'pPercST': -1,
            'pPercIPI': -1,
            'pPreçoVenda': -1,
            'pExige Conferencia': 'N',
            'pMarkup': -1,
            'pFrete': -1,
            'pDesconto': -1,
            'pEmpresa': '101'
        }
        
        for coluna, valor_padrao in campos_padrao.items():
            if coluna not in self.df.columns:
                continue
            
            linhas_vazias = []
            for idx, valor in enumerate(self.df[coluna]):
                if pd.isna(valor) or str(valor).strip() == '':
                    linhas_vazias.append(idx + 2)
            
            if linhas_vazias:
                sugestao = f"{coluna}: {len(linhas_vazias)} células vazias podem usar valor padrão '{valor_padrao}'"
                self.avisos.append(sugestao)
                self.log(f"💡 {sugestao}")
        
        if not self.avisos:
            self.log("✅ Todos os campos com valores padrão estão preenchidos")
    
    def validar_pOrigem_CST(self):
        """Valida a coluna pOrigem CST (deve ser 0 ou 2)"""
        if 'pOrigem CST' not in self.df.columns:
            return
        
        self.log("\n🌍 Validando pOrigem CST...")
        valores_invalidos = []
        
        for idx, valor in enumerate(self.df['pOrigem CST']):
            if pd.isna(valor):
                valores_invalidos.append(f"Linha {idx + 2}: valor vazio")
            elif str(valor).strip() not in ['0', '2']:
                valores_invalidos.append(f"Linha {idx + 2}: '{valor}' (deve ser 0 ou 2)")
        
        if valores_invalidos:
            erro = f"pOrigem CST com valores incorretos: {len(valores_invalidos)} casos"
            self.erros.append(erro)
            self.log(f"❌ {erro}")
            for linha in valores_invalidos[:5]:
                self.log(f"   {linha}")
            if len(valores_invalidos) > 5:
                self.log(f"   ... e mais {len(valores_invalidos) - 5} casos")
        else:
            self.log("✅ pOrigem CST: Todos os valores estão corretos (0 ou 2)")
    
    def validar_valores_numericos(self):
        """Valida campos que devem ser numéricos"""
        campos_numericos = [
            'pTamanho', 'pSegmento', 'pFamilia', 'pSubFamilia', 'pMúltiplo', 
            'pM²/Pallet', 'pQUANTIDADE NA EMBALAGEM', 'pPercST', 'pPercIPI', 
            'pPreçoVenda', 'pMarkup', 'pFrete', 'pCodigoSA', 'pDesconto'
            # Removido 'pNCM' - tem validação específica própria
        ]
        for coluna in campos_numericos:
            if coluna not in self.df.columns:
                continue
            valores_invalidos = []
            for idx, valor in enumerate(self.df[coluna]):
                if pd.isna(valor):
                    continue
                try:
                    valor_str = str(valor).replace(',', '.')
                    float(valor_str)
                except (ValueError, TypeError):
                    valores_invalidos.append(f"Linha {idx + 2}: '{valor}' (não é numérico)")
            if valores_invalidos:
                erro = f"{coluna}: {len(valores_invalidos)} valores não numéricos"
                self.erros.append(erro)

    def remover_acentos_e_caracteres_especiais(self, texto):
        """Função para remover acentos e caracteres especiais de um texto"""
        nfkd = unicodedata.normalize('NFKD', texto)
        texto_sem_acentos = ''.join([c for c in nfkd if not unicodedata.combining(c)])
        texto_limpo = re.sub(r'[^a-zA-Z0-9]', '', texto_sem_acentos)
        return texto_limpo.lower()  # Faz tudo minúsculo para comparação

    def validar_pNCM(self):
        """Validação específica para coluna pNCM - deve ser apenas numérica"""
        if 'pNCM' not in self.df.columns:
            self.avisos.append("⚠️ Coluna pNCM não encontrada")
            return
        
        self.log("🔍 Validando coluna pNCM...")
        valores_invalidos = []
        valores_corrigidos = 0
        
        for idx, valor in enumerate(self.df['pNCM']):
            if pd.isna(valor):
                continue
                
            valor_original = str(valor).strip()
            
            # Verificar se contém texto (como "BATATAS")
            if not valor_original.replace('.', '').replace(',', '').isdigit():
                # Se contém letras ou caracteres especiais
                if any(c.isalpha() for c in valor_original):
                    valores_invalidos.append(f"Linha {idx + 2}: '{valor_original}' (contém texto - deve ser apenas numérico)")
                    # Opcional: substituir por valor padrão ou deixar vazio
                    self.df.at[idx, 'pNCM'] = ''  # ou pd.NA
                    valores_corrigidos += 1
                else:
                    # Tentar converter números com vírgula/ponto
                    try:
                        valor_numerico = float(valor_original.replace(',', '.'))
                        # Converter para inteiro se for NCM (geralmente são códigos inteiros)
                        if valor_numerico == int(valor_numerico):
                            self.df.at[idx, 'pNCM'] = int(valor_numerico)
                            valores_corrigidos += 1
                    except (ValueError, TypeError):
                        valores_invalidos.append(f"Linha {idx + 2}: '{valor_original}' (formato inválido)")
                        self.df.at[idx, 'pNCM'] = ''
                        valores_corrigidos += 1
        
        if valores_invalidos:
            erro = f"pNCM: {len(valores_invalidos)} valores com texto/formato inválido encontrados"
            self.erros.append(erro)
            self.log(f"❌ {erro}")
            
            # Log detalhado dos primeiros 5 erros
            for i, erro_detalhe in enumerate(valores_invalidos[:5]):
                self.log(f"   • {erro_detalhe}")
            
            if len(valores_invalidos) > 5:
                self.log(f"   • ... e mais {len(valores_invalidos) - 5} erros")
        
        if valores_corrigidos > 0:
            self.avisos.append(f"⚠️ pNCM: {valores_corrigidos} valores foram limpos/corrigidos")
            self.log(f"🔧 {valores_corrigidos} valores na coluna pNCM foram corrigidos")
        
        if not valores_invalidos:
            self.log("✅ Coluna pNCM validada - todos os valores são numéricos")

    def gerar_relatorio_final(self):
        """Gera um relatório final completo da validação"""
        self.log("="*80)
        self.log("📊 RELATÓRIO FINAL DE VALIDAÇÃO - PRODUTOS")
        self.log("="*80)
        
        self.log(f"📁 Arquivo: {os.path.basename(self.arquivo)}")
        self.log(f"📊 Total de linhas: {len(self.df) if self.df is not None else 0}")
        self.log(f"📋 Colunas esperadas: {len(self.colunas_esperadas)}")
        self.log(f"❌ Total de erros: {len(self.erros)}")
        self.log(f"⚠️  Total de avisos: {len(self.avisos)}")
        
        status = "🎉 ARQUIVO VÁLIDO" if len(self.erros) == 0 else "❌ ARQUIVO COM PROBLEMAS"
        self.log(f"\n{status}")
        
        nome_relatorio = f"relatorio_produtos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(nome_relatorio, 'w', encoding='utf-8') as f:
            f.write("RELATÓRIO DE VALIDAÇÃO - PLANILHA DE PRODUTOS\n")
            f.write("="*60 + "\n\n")
            f.write(f"Arquivo: {self.arquivo}\n")
            f.write(f"Data da validação: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(f"Total de linhas: {len(self.df) if self.df is not None else 0}\n")
            f.write(f"Total de erros: {len(self.erros)}\n")
            f.write(f"Total de avisos: {len(self.avisos)}\n\n")
            
            if self.erros:
                f.write("ERROS CRÍTICOS ENCONTRADOS:\n")
                for erro in self.erros:
                    f.write(f"{erro}\n")
            
            if self.avisos:
                f.write("AVISOS E SUGESTÕES:\n")
                for aviso in self.avisos:
                    f.write(f"{aviso}\n")

        self.log(f"\n💾 Relatório detalhado salvo em: {nome_relatorio}")
        return len(self.erros) == 0

    # NOVO MÉTODO ADICIONADO PARA COMPATIBILIDADE COM APP.PY
    def gerar_relatorio(self):
        """Gera relatório no formato esperado pelo app.py"""
        import re
        total_linhas = len(self.df) if self.df is not None else 0
        
        # Contar linhas inválidas de forma mais precisa
        linhas_invalidas = 0
        
        # Contar erros que mencionam linhas específicas
        for erro in self.erros:
            if 'Linha' in erro:
                linhas_invalidas += 1
            elif 'pNCM:' in erro and 'valores com texto/formato inválido' in erro:
                # Extrair número de linhas inválidas do erro de pNCM
                match = re.search(r'pNCM: (\d+) valores', erro)
                if match:
                    linhas_invalidas += int(match.group(1))
            elif 'pOrigem CST com valores incorretos:' in erro:
                # Extrair número de linhas inválidas do erro de pOrigem CST
                match = re.search(r'valores incorretos: (\d+) casos', erro)
                if match:
                    linhas_invalidas += int(match.group(1))
        
        linhas_validas = total_linhas - linhas_invalidas
        
        relatorio = {
            'resumo': {
                'arquivo': os.path.basename(self.arquivo),
                'total_linhas': total_linhas,
                'linhas_validas': linhas_validas,
                'linhas_invalidas': linhas_invalidas,
                'percentual_validas': round((linhas_validas / total_linhas) * 100, 2) if total_linhas > 0 else 0,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'erros': self.erros,
            'warnings': self.avisos,
            'logs': self.logs
        }
        
        return relatorio

    def executar_validacao_completa(self):
        """Executa todas as validações em sequência"""
        # Carrega o arquivo
        if not self.carregar_arquivo():
            return self.gerar_relatorio()  # Retorna relatório mesmo com erro
        
        # Executa todas as validações
        estrutura_ok = self.verificar_estrutura_colunas()
        if estrutura_ok:
            self.validar_colunas_obrigatorias()
            self.aplicar_valores_padrao()
            self.validar_pOrigem_CST()
            self.validar_pNCM()  # Nova validação específica
            self.validar_valores_numericos()
        
        # Gera o relatório final (seu método original)
        self.gerar_relatorio_final()
        
        # Retorna o relatório no formato esperado pelo app.py
        return self.gerar_relatorio()
