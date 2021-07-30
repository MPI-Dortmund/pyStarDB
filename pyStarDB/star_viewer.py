import sys
import pandas
from PyQt5 import QtCore, QtWidgets
from pyStarDB import sp_pystardb as pystar


class Widget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent=None)
        layout1 = QtWidgets.QGridLayout()
        layout2 = QtWidgets.QGridLayout()
        final_layout = QtWidgets.QHBoxLayout(self)

        self.model : QtCore.QAbstractTableModel
        self.data : pandas.DataFrame()
        self.star : pystar.StarFile()

        self.pathLE1 = QtWidgets.QLineEdit(self)
        self.pathLE2 = QtWidgets.QLineEdit(self)
        self.pathLE3 = QtWidgets.QLineEdit(self)
        self.pathLE4 = QtWidgets.QLineEdit(self)

        self.loadBtn1 = QtWidgets.QPushButton("Select File", self)
        self.loadBtn2 = QtWidgets.QPushButton("Delete Column", self)
        self.loadBtn3 = QtWidgets.QPushButton("Delete Row", self)
        self.loadBtn4 = QtWidgets.QPushButton("Write New File", self)

        layout1.addWidget(self.pathLE1 , 0, 0)
        layout1.addWidget(self.loadBtn1, 0, 1)

        layout1.addWidget(self.pathLE2, 1, 0)
        layout1.addWidget(self.loadBtn2, 1, 1)

        layout1.addWidget(self.pathLE3, 2, 0)
        layout1.addWidget(self.loadBtn3, 2, 1)

        layout1.addWidget(self.pathLE4, 3, 0)
        layout1.addWidget(self.loadBtn4, 3, 1)

        self.loadBtn1.clicked.connect(self.loadFile)
        self.loadBtn2.clicked.connect(self.DeleteColumn)
        self.loadBtn3.clicked.connect(self.DeleteRow)
        self.loadBtn4.clicked.connect(self.Write_Updated_File)

        self.pandasTv = QtWidgets.QTableView(self)
        self.pandasTv.setSortingEnabled(True)
        layout2.addWidget(self.pandasTv, 0 ,0)

        final_layout.addLayout(layout1,stretch=1)
        final_layout.addLayout(layout2, stretch=3)
        self.resize(840, 680)

    def loadFile(self):
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "", "STAR Files (*.star)");
        self.pathLE1.setText(fileName)
        self.star = pystar.StarFile(fileName)
        try:
            self.data = self.star["particles"]
        except KeyError:
            self.data = self.star[""]

        self.model = PandasModel(self.data)
        self.pandasTv.setModel(self.model)

    def DeleteColumn(self):
        print("Delete Column is being called")
        # print("Key to delete is ", self.pathLE2.text())
        # self.data = pandas.DataFrame([[0, 1, 5], [2, 3, 4]], columns=['_col1', '_col2', '_col3'])
        try:
            self.data.drop(self.pathLE2.text(), inplace=True, axis = 1)
            self.model = PandasModel(self.data)
            self.pandasTv.setModel(self.model)
        except KeyError:
            print("No column found with that name {} to delete".format(self.pathLE2.text()))

    def DeleteRow(self):
        print("Deleter Row is being called")
        try:
            self.data.drop(int(self.pathLE3.text()), inplace=True, axis=0)
            self.model = PandasModel(self.data)
            self.pandasTv.setModel(self.model)
        except KeyError :
            print("No row found that number {} to delete".format(int(self.pathLE3.text())))
        except ValueError:
            print("Please enter number, you entered {}".format(self.pathLE3.text()))

    def Write_Updated_File(self):
        print("Writing new star")
        self.star.update("particles", self.data, True)
        self.star.write_star_file(self.pathLE4.text())


###https://stackoverflow.com/questions/44603119/how-to-display-a-pandas-data-frame-with-pyqt5-pyside2
class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, df = pandas.DataFrame(), parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent=parent)
        super().__init__()
        self._df = df

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == QtCore.Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except (IndexError, ):
                return QtCore.QVariant()
        elif orientation == QtCore.Qt.Vertical:
            try:
                # return self.df.index.tolist()
                return self._df.index.tolist()[section]
            except (IndexError, ):
                return QtCore.QVariant()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if not index.isValid():
            return QtCore.QVariant()

        return QtCore.QVariant(str(self._df.iloc[index.row(), index.column()]))

    def setData(self, index, value, role):
        row = self._df.index[index.row()]
        col = self._df.columns[index.column()]
        if hasattr(value, 'toPyObject'):
            # PyQt4 gets a QVariant
            value = value.toPyObject()
        else:
            # PySide gets an unicode
            dtype = self._df[col].dtype
            if dtype != object:
                value = None if value == '' else dtype.type(value)
        self._df.set_value(row, col, value)
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.columns)

    def sort(self, column, order):
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(colname, ascending= order == QtCore.Qt.AscendingOrder, inplace=True)
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())