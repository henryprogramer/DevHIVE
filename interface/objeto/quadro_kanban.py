from PyQt5.QtWidgets import QInputDialog, QMainWindow, QLabel, QMessageBox

class QuadroKanbanWindow(QMainWindow):
    def __init__(self, quadro_id=None, controle_coluna=None, controle_card=None):
        super().__init__()
        self.quadro_id = quadro_id
        self.controle_coluna = controle_coluna
        self.controle_card = controle_card
        
        self.setWindowTitle(f"Quadro Kanban - ID {self.quadro_id}")
        self.resize(800, 600)
        self.setCentralWidget(QLabel(f"Conteúdo do Quadro ID: {self.quadro_id}"))

    @staticmethod
    def criar_novo_quadro(parent):
        nome, ok = QInputDialog.getText(parent, "Novo Quadro", "Nome do quadro:")
        return nome.strip() if (ok and nome.strip()) else None

    # --- NOVOS MÉTODOS PARA EDIT E DEL ---

    @staticmethod
    def editar_nome_quadro(parent, nome_atual):
        """Abre diálogo para editar o nome existente"""
        nome, ok = QInputDialog.getText(
            parent, 
            "Editar Quadro", 
            "Novo nome do quadro:", 
            text=nome_atual
        )
        return nome.strip() if (ok and nome.strip()) else None

    @staticmethod
    def confirmar_exclusao(parent, nome_quadro):
        """Abre confirmação de exclusão"""
        resposta = QMessageBox.question(
            parent,
            "Excluir Quadro",
            # Wit: Um toque de clareza sobre o perigo da ação
            f"Tem certeza que deseja excluir o quadro '{nome_quadro}'?\nEsta ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return resposta == QMessageBox.Yes

    def show(self):
        print(f"Abrindo janela visual do quadro: {self.quadro_id}")
        super().show()