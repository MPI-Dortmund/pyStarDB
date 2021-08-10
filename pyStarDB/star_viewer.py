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

        self.loadBtn5 = QtWidgets.QPushButton("String Replace", self)


        self.ColumnList = QtWidgets.QComboBox(self)
        self.RowList = QtWidgets.QComboBox(self)

        self.ColumnList1 = QtWidgets.QComboBox(self)

        self.ColumnList.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.ColumnList1.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.RowList.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        layout1.addWidget(self.pathLE1 , 0, 0)
        layout1.addWidget(self.loadBtn1, 0, 1)

        # layout1.addWidget(self.pathLE2, 1, 0)
        layout1.addWidget(self.loadBtn2, 1, 1)
        layout1.addWidget(self.ColumnList, 1, 0)

        layout1.addWidget(self.RowList, 2, 0)
        layout1.addWidget(self.loadBtn3, 2, 1)

        layout1.addWidget(self.pathLE4, 3, 0)
        layout1.addWidget(self.loadBtn4, 3, 1)


        layout1.addWidget(self.ColumnList1, 4, 0)
        layout1.addWidget(self.pathLE2, 4, 1)
        layout1.addWidget(self.pathLE3, 4, 2)
        layout1.addWidget(self.loadBtn5, 4, 3)


        self.loadBtn1.clicked.connect(self.loadFile)
        self.loadBtn2.clicked.connect(self.DeleteColumn)
        self.loadBtn3.clicked.connect(self.DeleteRow)
        self.loadBtn4.clicked.connect(self.Write_Updated_File)

        self.loadBtn5.clicked.connect(self.string_replace_me)

        self.pandasTv = QtWidgets.QTableView(self)
        self.pandasTv.setSortingEnabled(True)
        layout2.addWidget(self.pandasTv, 0 ,0)

        final_layout.addLayout(layout1,stretch=1)
        final_layout.addLayout(layout2, stretch=3)
        self.resize(840, 680)

    def string_replace_me(self):
        column_name = self.ColumnList1.currentText()
        current_str = self.pathLE2.text()
        replace_str = self.pathLE3.text()
        self.data[column_name] = self.data[column_name].str.replace(current_str, replace_str)


        self.updateKeys()
        self.updateRows()
        self.model = PandasModel(self.data)
        self.pandasTv.setModel(self.model)


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
        self.updateKeys()
        self.updateRows()

    def updateKeys(self):
        if self.data.empty:
            print("No data yet")
        else :
            self.ColumnList.clear()
            self.ColumnList1.clear()
            self.keylist = self.data.columns
            self.ColumnList.addItems(self.keylist)
            self.ColumnList1.addItems(self.keylist)

    def updateRows(self):
        # print("Index" , print(self.data.rows))
        if self.data.empty:
            print("No data yet")
        else :
            self.RowList.clear()
            self.numlist = [str(value) for value in self.data.index]
            self.RowList.addItems(self.numlist)

    def DeleteColumn(self):
        print("Delete Column is being called")
        # print("Key to delete is ", self.pathLE2.text())
        # self.data = pandas.DataFrame([[0, 1, 5], [2, 3, 4]], columns=['_col1', '_col2', '_col3'])
        try:
            self.data.drop(self.ColumnList.currentText(), inplace=True, axis = 1)
            self.model = PandasModel(self.data)
            self.pandasTv.setModel(self.model)
            self.updateKeys()
        except Exception as e :
            print(e)


    def DeleteRow(self):
        print("Deleter Row is being called")
        try:
            self.data.drop(int( self.RowList.currentText() ), inplace=True, axis=0)
            self.model = PandasModel(self.data)
            self.pandasTv.setModel(self.model)
            self.updateRows()
        except Exception as e:
            print(e)

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

def main():
    app = QtWidgets.QApplication(sys.argv)
    w = Widget()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()