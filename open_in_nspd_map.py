# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OpenNSPDMap
                                 A QGIS plugin
 Opens the current map extent in NSPD map
                              -------------------
        begin                : 2025-04-28
        copyright            : (C) 2025 Alexandr_Fedorov
        email                : rusorur@mail.ru
 ***************************************************************************/
"""

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (QAction, QFileDialog, QMessageBox, 
                                QDialog, QVBoxLayout, QCheckBox, QPushButton)
from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform, Qgis
import os
import subprocess
import math

class LayerSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Отображение слоев для охвата на сайте NSPD")
        self.layout = QVBoxLayout()
        
        # Список слоёв и их ID
        self.layers = {
            "Кадастровые округа": 36945,
            "Кадастровые районы": 36070,
            "Кадастровые кварталы": 36071,
            "Государственная граница Российской Федерации": 37313,
            "Субъекты Российской Федерации (линии)": 37314,
            "Субъекты Российской Федерации (полигоны)": 37315,
            "Муниципальные образования (полигональный)": 36278,
            "Муниципальные образования (линейный)": 36279,
            "Населённые пункты (полигоны)": 36281,
            "Населённые пункты (линии)": 37316,
            "Земельные участки из ЕГРН": 36048,
            "Земельные участки, образуемые по схеме расположения земельного участка": 37294,
            "Земельные участки, выставленные на аукцион": 37299,
            "Земельные участки, свободные от прав третьих лиц": 37298,
            "Земля для стройки ПКК": 849407,
            "Земля для туризма ПКК": 849453,
            "Земельные участки, образуемые по проекту межевания территории": 36473,
            "Здания": 36049,
            "Сооружения": 36328,
            "Объекты незавершенного строительства": 36329,
            "Единые недвижимые комплексы": 37433,
            "Предприятие как имущественный комплекс": 37434,
            "ЗОУИТ объектов культурного наследия": 37577,
            "ЗОУИТ объектов энергетики, связи, транспорта": 37578,
            "ЗОУИТ природных территорий": 37580,
            "ЗОУИТ охраняемых объектов и безопасности": 37579,
            "Иные ЗОУИТ": 37581,
            "Территориальные зоны": 36315,
            "Красные линии": 37293,
            "Береговые линии (границы водных объектов) (полигональный)": 36469,
            "Береговые линии (границы водных объектов) (линейный)": 36470,
        }
        
        self.checkboxes = {}
        
        # Загружаем сохранённые настройки
        self.settings = QSettings()
        self.active_layers = self.settings.value("OpenNSPDMap/ActiveLayers", [])
        if not self.active_layers:
            self.active_layers = []
        
        # Создаём чекбоксы для каждого слоя
        for name, layer_id in self.layers.items():
            cb = QCheckBox(name)
            cb.setChecked(str(layer_id) in self.active_layers)
            self.checkboxes[layer_id] = cb
            self.layout.addWidget(cb)
        
        # Кнопка сохранения
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self.save_settings)
        self.layout.addWidget(btn_save)
        
        self.setLayout(self.layout)
    
    def save_settings(self):
        active_layers = []
        for layer_id, cb in self.checkboxes.items():
            if cb.isChecked():
                active_layers.append(str(layer_id))
        
        self.settings.setValue("OpenNSPDMap/ActiveLayers", active_layers)
        self.accept()

class OpenInNSPDMapPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        settings_icon_path = os.path.join(self.plugin_dir, 'iconsetting.png')
        layers_icon_path = os.path.join(self.plugin_dir, 'iconlayers.png')
        
        # Кнопка "Открыть в NSPD Map"
        self.open_action = QAction(QIcon(icon_path), 'Открыть в NSPD Map', self.iface.mainWindow())
        self.open_action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.open_action)
        self.actions.append(self.open_action)

        # Кнопка "Настройки слоёв" (вторая)
        self.layers_action = QAction(QIcon(layers_icon_path), 'Отображение слоев для охвата на сайте NSPD', self.iface.mainWindow())
        self.layers_action.triggered.connect(self.open_layers_dialog)
        self.iface.addToolBarIcon(self.layers_action)
        self.actions.append(self.layers_action)

        # Кнопка "Настройки браузера" (третья)
        self.settings_action = QAction(QIcon(settings_icon_path), 'Настройки браузера', self.iface.mainWindow())
        self.settings_action.triggered.connect(self.open_settings_dialog)
        self.iface.addToolBarIcon(self.settings_action)
        self.actions.append(self.settings_action)

    def unload(self):
        for action in self.actions:
            self.iface.removeToolBarIcon(action)
            self.iface.mainWindow().removeAction(action)
        self.actions.clear()

    def run(self):
        canvas = self.iface.mapCanvas()
        extent = canvas.extent()
        current_crs = canvas.mapSettings().destinationCrs()
        target_crs = QgsCoordinateReferenceSystem('EPSG:3857')
        transform = QgsCoordinateTransform(current_crs, target_crs, QgsProject.instance())
        transformed_extent = transform.transformBoundingBox(extent)

        center_x = (transformed_extent.xMinimum() + transformed_extent.xMaximum()) / 2
        center_y = (transformed_extent.yMinimum() + transformed_extent.yMaximum()) / 2
        zoom = self._calculate_zoom_level()

        # Получаем активные слои из настроек
        settings = QSettings()
        active_layers = settings.value("OpenNSPDMap/ActiveLayers", [])
        layers_param = "%2C".join(active_layers) if active_layers else ""

        nspd_url = (
            f"https://nspd.gov.ru/map?"
            f"zoom={zoom}&coordinate_x={center_x}&coordinate_y={center_y}"
            f"&theme_id=1&is_copy_url=true&active_layers={layers_param}"
        )

        browser_path = settings.value("OpenNSPDMap/YandexPath", type=str)

        if browser_path and os.path.exists(browser_path):
            try:
                subprocess.Popen([browser_path, nspd_url])
            except Exception as e:
                self.iface.messageBar().pushMessage(
                    "Ошибка запуска браузера", str(e), level=Qgis.Critical
                )
        else:
            self.iface.messageBar().pushMessage(
                "Не задан путь к Yandex Browser",
                "Перейдите в настройки плагина и укажите путь к Yandex.Браузеру",
                level=Qgis.Warning
            )

    def _calculate_zoom_level(self):
        """
        Расчет zoom уровня для NSPD карты на основе масштаба QGIS.
        Для масштаба 1:10 (10 метров) возвращает zoom=18.666666666666664
        """
        canvas = self.iface.mapCanvas()
        scale = canvas.scale()
        
        # Конвертируем масштаб в знаменатель (убираем "1:")
        if isinstance(scale, str):
            scale = float(scale.split(':')[-1])
        
        # Формула для расчета zoom: zoom = log2(559082264.028 / scale)
        # Где 559082264.028 - это масштаб для zoom=0 в веб-меркаторе
        
        # Для масштаба 10 метров (1:10) должно быть 18.666666666666664
        zoom = math.log2(559082264.028 / scale)
        
        # Ограничиваем zoom в разумных пределах (0-20)
        zoom = max(0, min(20, zoom))
        
        return zoom

    def open_settings_dialog(self):
        settings = QSettings()
        current_path = settings.value("OpenNSPDMap/YandexPath", "")

        file_path, _ = QFileDialog.getOpenFileName(
            self.iface.mainWindow(),
            "Укажите путь к Yandex Browser",
            current_path or "",
            "Исполняемые файлы (*.exe);;Все файлы (*)"
        )

        if file_path:
            settings.setValue("OpenNSPDMap/YandexPath", file_path)
            QMessageBox.information(
                self.iface.mainWindow(),
                "Настройки сохранены",
                "Путь к Yandex.Браузеру успешно сохранён."
            )
    
    def open_layers_dialog(self):
        dialog = LayerSettingsDialog(self.iface.mainWindow())
        dialog.exec_()