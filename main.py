import customtkinter as ctk
from tkinter import filedialog, messagebox
import pdfplumber
import pandas as pd
import re
import os
import threading

# Configuração do tema
ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuração da janela principal
        self.title("Extrator de Ficha de Registro - Premium")
        self.geometry("500x450")
        self.resizable(False, False)

        # Layout
        self.create_widgets()

    def create_widgets(self):
        # Título
        self.label_title = ctk.CTkLabel(self, text="Extrator de PDF", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_title.pack(pady=(30, 10))

        self.label_subtitle = ctk.CTkLabel(self, text="Extração de dados automatizada e segura", font=ctk.CTkFont(size=14))
        self.label_subtitle.pack(pady=(0, 20))

        # Frame de opções
        self.frame_options = ctk.CTkFrame(self)
        self.frame_options.pack(pady=10, padx=20, fill="x")

        self.label_format = ctk.CTkLabel(self.frame_options, text="Formato de Saída:", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_format.pack(pady=(15, 5))

        self.formato_var = ctk.StringVar(value="Excel")
        
        self.radio_excel = ctk.CTkRadioButton(self.frame_options, text="Excel (.xlsx)", variable=self.formato_var, value="Excel")
        self.radio_excel.pack(pady=5)
        
        self.radio_csv = ctk.CTkRadioButton(self.frame_options, text="CSV (;)", variable=self.formato_var, value="CSV")
        self.radio_csv.pack(pady=5)
        
        self.radio_txt = ctk.CTkRadioButton(self.frame_options, text="TXT (|)", variable=self.formato_var, value="TXT")
        self.radio_txt.pack(pady=(5, 15))

        # Botão de Ação
        self.btn_action = ctk.CTkButton(
            self, 
            text="Selecionar PDF e Iniciar", 
            command=self.iniciar_thread,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.btn_action.pack(pady=20, padx=20, fill="x")

        # Barra de Progresso
        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate")
        self.progress_bar.pack(pady=10, padx=20, fill="x")
        self.progress_bar.set(0)

        # Status
        self.label_status = ctk.CTkLabel(self, text="Aguardando início...", text_color="gray")
        self.label_status.pack(pady=(0, 20))

    def iniciar_thread(self):
        self.btn_action.configure(state="disabled")
        thread = threading.Thread(target=self.executar_processo)
        thread.start()

    def update_status(self, message, progress=None):
        self.label_status.configure(text=message)
        if progress is not None:
            self.progress_bar.set(progress)
        self.update_idletasks()

    def executar_processo(self):
        try:
            pdf_path = filedialog.askopenfilename(
                title="Selecionar PDF",
                filetypes=[("Arquivos PDF", "*.pdf")]
            )

            if not pdf_path:
                self.btn_action.configure(state="normal")
                self.update_status("Seleção cancelada.")
                return

            self.update_status("Lendo PDF...", 0.1)

            df = self.processar_pdf(pdf_path)

            if df is None or df.empty:
                 self.btn_action.configure(state="normal")
                 return

            self.update_status("Salvando arquivo...", 0.9)
            
            formato = self.formato_var.get()
            extensao = {"Excel": ".xlsx", "CSV": ".csv", "TXT": ".txt"}[formato]

            save_path = filedialog.asksaveasfilename(
                defaultextension=extensao,
                filetypes=[("Arquivo", "*" + extensao)]
            )

            if not save_path:
                 self.update_status("Salvamento cancelado.")
                 self.btn_action.configure(state="normal")
                 return

            self.exportar(df, save_path, formato)
            
            self.update_status("Concluído com Sucesso!", 1.0)
            messagebox.showinfo("Sucesso", "Arquivo exportado com sucesso!")

        except Exception as e:
            self.update_status("Erro no processamento.")
            messagebox.showerror("Erro Crítico", f"Ocorreu um erro inesperado:\n{str(e)}")
        
        finally:
            self.btn_action.configure(state="normal")

    # ==============================
    # LÓGICA DE NEGÓCIO
    # ==============================
    def processar_pdf(self, pdf_path):
        texto_completo = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_paginas = len(pdf.pages)
                if total_paginas == 0:
                    messagebox.showwarning("Aviso", "O PDF parece estar vazio ou corrompido.")
                    return None

                for i, pagina in enumerate(pdf.pages):
                    try:
                        texto = pagina.extract_text()
                        if texto:
                            texto_completo += texto + "\n"
                        
                        # Atualiza progresso da leitura (vai de 0.1 a 0.5)
                        progresso = 0.1 + (0.4 * ((i + 1) / total_paginas))
                        self.update_status(f"Lendo página {i+1} de {total_paginas}...", progresso)
                        
                    except Exception as e:
                        print(f"Erro ao ler página {i+1}: {e}")
                        # Não para o processo, apenas loga e continua
                        continue

        except Exception as e:
            messagebox.showerror("Erro ao abrir PDF", str(e))
            return None

        self.update_status("Processando dados...", 0.6)
        
        texto_tratado = self.remover_cabecalho(texto_completo)
        funcionarios = self.separar_funcionarios(texto_tratado)

        lista_dados = []
        total_funcionarios = len(funcionarios)

        for i, funcionario in enumerate(funcionarios):
            try:
                dados = self.extrair_campos(funcionario)
                lista_dados.append(dados)
                
                # Atualiza progresso do processamento (vai de 0.6 a 0.9)
                progresso = 0.6 + (0.3 * ((i + 1) / total_funcionarios))
                self.update_status(f"Processando registro {i+1}...", progresso)
                
            except Exception as e:
                print(f"Erro ao processar registro {i}: {e}")
                continue

        return pd.DataFrame(lista_dados)

    def remover_cabecalho(self, texto):
        match = re.search(r'Código\s*\n?\s*\d+', texto)
        if match:
            return texto[match.start():]
        return texto

    def separar_funcionarios(self, texto):
        padrao = r'Código\s*\n?\s*\d+'
        ids = re.findall(padrao, texto)
        blocos = re.split(padrao, texto)

        funcionarios = []
        if len(blocos) > len(ids): 
            # Ajuste de listas
            blocos = blocos[1:] 

        for i in range(len(ids)):
            if i < len(blocos):
                bloco = ids[i] + "\n" + blocos[i]
                funcionarios.append(bloco)

        return funcionarios

    def extrair_campos(self, texto_funcionario):
        dados = {}
        padrao = re.findall(r'([A-Za-zÀ-ÿ0-9\s\/\-\(\)\.]+)\s*:\s*(.+)', texto_funcionario)

        for campo, valor in padrao:
            campo_limpo = (
                campo.strip()
                .replace(" ", "_")
                .replace("/", "_")
                .replace("-", "_")
                .replace(".", "")
            )
            dados[campo_limpo] = valor.strip()

        if "ID" not in dados:
            match_codigo = re.search(r'Código\s*\n?\s*(\d+)', texto_funcionario)
            if match_codigo:
                dados['ID'] = match_codigo.group(1)

        return dados

    def exportar(self, df, caminho, formato):
        if formato == "Excel":
            df.to_excel(caminho, index=False)
        elif formato == "CSV":
            df.to_csv(caminho, index=False, sep=";", encoding="utf-8-sig")
        elif formato == "TXT":
            df.to_csv(caminho, index=False, sep="|", encoding="utf-8")


if __name__ == "__main__":
    app = App()
    app.mainloop()
