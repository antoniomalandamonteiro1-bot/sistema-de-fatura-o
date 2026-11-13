
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime



LIMITE_BONUS = 100000
TAXA_BONUS = 0.10
IDADE_IDOSA = 60

conexao = sqlite3.connect("loja.db")
cursor = conexao.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS facturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT,
    genero TEXT,
    idade INTEGER,
    gravida TEXT,
    deficiencia TEXT,
    subtotal REAL,
    bonus REAL,
    total REAL,
    prioridade TEXT,
    data TEXT
)
""")

conexao.commit()

produtos = []


# =====================================
# FUNÇÕES
# =====================================

def formatar(valor):
    return f"{valor:,.2f} Kz"


def adicionar_produto():

    nome = entrada_produto.get().strip()

    try:
        quantidade = float(entrada_quantidade.get().replace(",", "."))
        preco = float(entrada_preco.get().replace(",", "."))

        if not nome or quantidade <= 0 or preco < 0:
            raise ValueError

    except ValueError:
        messagebox.showerror(
            "Erro",
            "Introduza correctamente o produto, quantidade e preço."
        )
        return

    total = quantidade * preco

    produtos.append({
        "nome": nome,
        "quantidade": quantidade,
        "preco": preco,
        "total": total
    })

    tabela.insert(
        "",
        "end",
        values=(
            nome,
            quantidade,
            formatar(preco),
            formatar(total)
        )
    )

    entrada_produto.delete(0, tk.END)
    entrada_quantidade.delete(0, tk.END)
    entrada_quantidade.insert(0, "1")
    entrada_preco.delete(0, tk.END)

    calcular_total()


def remover_produto():

    selecionado = tabela.selection()

    if not selecionado:
        messagebox.showwarning(
            "Atenção",
            "Seleccione um produto."
        )
        return

    indices = sorted(
        [tabela.index(item) for item in selecionado],
        reverse=True
    )

    for indice in indices:
        produtos.pop(indice)

    for item in tabela.get_children():
        tabela.delete(item)

    for p in produtos:
        tabela.insert(
            "",
            "end",
            values=(
                p["nome"],
                p["quantidade"],
                formatar(p["preco"]),
                formatar(p["total"])
            )
        )

    calcular_total()


def calcular_total():

    subtotal = sum(p["total"] for p in produtos)

    if subtotal > LIMITE_BONUS:
        bonus = subtotal * TAXA_BONUS
    else:
        bonus = 0

    total = subtotal - bonus

    label_subtotal.config(
        text="Subtotal: " + formatar(subtotal)
    )

    label_bonus.config(
        text="Bónus: " + formatar(bonus)
    )

    label_total.config(
        text="TOTAL A PAGAR: " + formatar(total)
    )

    return subtotal, bonus, total


def guardar_factura():

    cliente = entrada_cliente.get().strip()
    genero = combo_genero.get()

    if not cliente:
        messagebox.showerror(
            "Erro",
            "Introduza o nome do cliente."
        )
        return

    if not produtos:
        messagebox.showerror(
            "Erro",
            "Adicione pelo menos um produto."
        )
        return

    try:
        idade = int(entrada_idade.get())

        if idade < 0 or idade > 120:
            raise ValueError

    except ValueError:
        messagebox.showerror(
            "Erro",
            "Introduza uma idade válida."
        )
        return

    gravida = "Sim" if var_gravida.get() else "Não"

    deficiencia = (
        "Sim" if var_deficiencia.get() else "Não"
    )

    # Cálculo da factura
    subtotal, bonus, total = calcular_total()

    # Identificação da prioridade
    if (
        var_gravida.get()
        or var_deficiencia.get()
        or idade >= IDADE_IDOSA
    ):
        prioridade = "PRIORITÁRIO"
    else:
        prioridade = "NORMAL"

    data = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    cursor.execute("""
        INSERT INTO facturas
        (cliente, genero, idade, gravida,
         deficiencia, subtotal, bonus,
         total, prioridade, data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cliente,
        genero,
        idade,
        gravida,
        deficiencia,
        subtotal,
        bonus,
        total,
        prioridade,
        data
    ))

    conexao.commit()

    numero = cursor.lastrowid

    factura = f"""
========== FACTURA ==========

Número: {numero}
Cliente: {cliente}
Género: {genero}
Data: {data}

---------- PRODUTOS ----------
"""

    for p in produtos:
        factura += (
            f"\n{p['nome']} | "
            f"{p['quantidade']} x "
            f"{formatar(p['preco'])} = "
            f"{formatar(p['total'])}"
        )

    factura += f"""

------------------------------
Subtotal: {formatar(subtotal)}
Bónus 10%: {formatar(bonus)}

TOTAL A PAGAR: {formatar(total)}

Atendimento: {prioridade}

==============================
Obrigado pela preferência!
"""

    messagebox.showinfo(
        "Factura registada",
        factura
    )

    limpar()
    atualizar_historico()


def limpar():

    entrada_cliente.delete(0, tk.END)
    entrada_idade.delete(0, tk.END)
    entrada_idade.insert(0, "25")

    combo_genero.current(0)

    var_gravida.set(False)
    var_deficiencia.set(False)

    produtos.clear()

    for item in tabela.get_children():
        tabela.delete(item)

    calcular_total()


def atualizar_historico():

    for item in historico.get_children():
        historico.delete(item)

    cursor.execute("""
        SELECT id, cliente, subtotal,
               bonus, total, prioridade, data
        FROM facturas
        ORDER BY id DESC
    """)

    for registo in cursor.fetchall():

        historico.insert(
            "",
            "end",
            values=(
                registo[0],
                registo[1],
                formatar(registo[2]),
                formatar(registo[3]),
                formatar(registo[4]),
                registo[5],
                registo[6]
            )
        )




janela = tk.Tk()

janela.title(
    "Sistema de Facturação - Loja Alimentar"
)

janela.geometry("1100x720")

janela.configure(bg="#edf2f7")

titulo = tk.Label(
    janela,
    text="SISTEMA DE FACTURAÇÃO",
    font=("Arial", 22, "bold"),
    bg="#123456",
    fg="white",
    pady=15
)

titulo.pack(fill="x")


abas = ttk.Notebook(janela)
abas.pack(fill="both", expand=True, padx=10, pady=10)

aba_venda = ttk.Frame(abas, padding=10)
aba_historico = ttk.Frame(abas, padding=10)

abas.add(aba_venda, text="Nova Factura")
abas.add(aba_historico, text="Histórico")




frame_cliente = ttk.LabelFrame(
    aba_venda,
    text="Dados do Cliente",
    padding=10
)

frame_cliente.pack(fill="x", pady=5)

ttk.Label(
    frame_cliente,
    text="Nome do Cliente:"
).grid(row=0, column=0, padx=5, pady=5)

entrada_cliente = ttk.Entry(
    frame_cliente,
    width=30
)

entrada_cliente.grid(row=0, column=1, padx=5)

ttk.Label(
    frame_cliente,
    text="Género:"
).grid(row=0, column=2, padx=5)

combo_genero = ttk.Combobox(
    frame_cliente,
    values=["Feminino", "Masculino", "Outro"],
    state="readonly",
    width=20
)

combo_genero.current(0)
combo_genero.grid(row=0, column=3, padx=5)

ttk.Label(
    frame_cliente,
    text="Idade:"
).grid(row=1, column=0, padx=5)

entrada_idade = ttk.Entry(
    frame_cliente,
    width=10
)

entrada_idade.insert(0, "25")
entrada_idade.grid(row=1, column=1, sticky="w", padx=5)

var_gravida = tk.BooleanVar()

ttk.Checkbutton(
    frame_cliente,
    text="Mulher grávida",
    variable=var_gravida
).grid(row=1, column=2, padx=5)

var_deficiencia = tk.BooleanVar()

ttk.Checkbutton(
    frame_cliente,
    text="Pessoa com deficiência",
    variable=var_deficiencia
).grid(row=1, column=3, padx=5)




frame_produto = ttk.LabelFrame(
    aba_venda,
    text="Registo de Produtos",
    padding=10
)

frame_produto.pack(fill="x", pady=10)

ttk.Label(
    frame_produto,
    text="Produto:"
).grid(row=0, column=0)

entrada_produto = ttk.Entry(
    frame_produto,
    width=25
)

entrada_produto.grid(row=0, column=1, padx=5)

ttk.Label(
    frame_produto,
    text="Quantidade:"
).grid(row=0, column=2)

entrada_quantidade = ttk.Entry(
    frame_produto,
    width=10
)

entrada_quantidade.insert(0, "1")
entrada_quantidade.grid(row=0, column=3, padx=5)

ttk.Label(
    frame_produto,
    text="Preço (Kz):"
).grid(row=0, column=4)

entrada_preco = ttk.Entry(
    frame_produto,
    width=15
)

entrada_preco.grid(row=0, column=5, padx=5)

ttk.Button(
    frame_produto,
    text="Adicionar",
    command=adicionar_produto
).grid(row=0, column=6, padx=5)


tabela = ttk.Treeview(
    aba_venda,
    columns=("produto", "quantidade", "preco", "total"),
    show="headings",
    height=9
)

tabela.heading("produto", text="Produto")
tabela.heading("quantidade", text="Quantidade")
tabela.heading("preco", text="Preço Unitário")
tabela.heading("total", text="Total")

tabela.pack(fill="both", expand=True, pady=10)




frame_total = ttk.Frame(aba_venda)
frame_total.pack(fill="x", pady=5)

label_subtotal = ttk.Label(
    frame_total,
    text="Subtotal: 0,00 Kz",
    font=("Arial", 11)
)

label_subtotal.pack(anchor="e")

label_bonus = ttk.Label(
    frame_total,
    text="Bónus: 0,00 Kz",
    font=("Arial", 11)
)

label_bonus.pack(anchor="e")

label_total = ttk.Label(
    frame_total,
    text="TOTAL A PAGAR: 0,00 Kz",
    font=("Arial", 15, "bold"),
    foreground="green"
)

label_total.pack(anchor="e")




frame_botoes = ttk.Frame(aba_venda)
frame_botoes.pack(fill="x", pady=10)

ttk.Button(
    frame_botoes,
    text="Remover Produto",
    command=remover_produto
).pack(side="left", padx=5)

ttk.Button(
    frame_botoes,
    text="Guardar Factura",
    command=guardar_factura
).pack(side="left", padx=5)

ttk.Button(
    frame_botoes,
    text="Limpar",
    command=limpar
).pack(side="left", padx=5)




historico = ttk.Treeview(
    aba_historico,
    columns=(
        "id", "cliente", "subtotal",
        "bonus", "total", "prioridade", "data"
    ),
    show="headings"
)

colunas = [
    ("id", "Nº", 50),
    ("cliente", "Cliente", 150),
    ("subtotal", "Subtotal", 120),
    ("bonus", "Bónus", 120),
    ("total", "Total", 120),
    ("prioridade", "Atendimento", 130),
    ("data", "Data", 160)
]

for coluna, titulo_coluna, largura in colunas:
    historico.heading(coluna, text=titulo_coluna)
    historico.column(coluna, width=largura)

historico.pack(fill="both", expand=True)

ttk.Button(
    aba_historico,
    text="Actualizar Histórico",
    command=atualizar_historico
).pack(pady=10)




atualizar_historico()
calcular_total()

janela.mainloop()

conexao.close()
