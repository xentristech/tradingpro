#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EXPORTADOR A GOOGLE SHEETS - ALGO TRADER V3
===========================================
Exporta métricas y trades a Google Sheets automáticamente
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

# Intentar importar gspread
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    logging.warning("gspread no instalado. Instala con: pip install gspread google-auth")

logger = logging.getLogger(__name__)

class GoogleSheetsExporter:
    """Exportador de datos a Google Sheets"""
    
    def __init__(self, credentials_file: str = "configs/google_credentials.json"):
        """
        Inicializa el exportador
        
        Args:
            credentials_file: Path al archivo de credenciales de Google
        """
        self.credentials_file = credentials_file
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        
        if GSPREAD_AVAILABLE and os.path.exists(credentials_file):
            self.initialize_client()
        else:
            logger.warning("Google Sheets no configurado. Revisa credenciales.")
            
    def initialize_client(self):
        """Inicializa el cliente de Google Sheets"""
        try:
            # Configurar scope
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Autenticar
            creds = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scope
            )
            
            self.client = gspread.authorize(creds)
            logger.info("Cliente de Google Sheets inicializado")
            
        except Exception as e:
            logger.error(f"Error inicializando Google Sheets: {e}")
            self.client = None
            
    def create_or_open_spreadsheet(self, spreadsheet_name: str = "AlgoTrader_Journal"):
        """Crea o abre una hoja de cálculo"""
        if not self.client:
            return False
            
        try:
            # Intentar abrir
            try:
                self.spreadsheet = self.client.open(spreadsheet_name)
                logger.info(f"Hoja '{spreadsheet_name}' abierta")
            except gspread.SpreadsheetNotFound:
                # Crear nueva
                self.spreadsheet = self.client.create(spreadsheet_name)
                logger.info(f"Hoja '{spreadsheet_name}' creada")
                
                # Compartir con email del usuario (opcional)
                # self.spreadsheet.share('tu_email@gmail.com', perm_type='user', role='writer')
                
            return True
            
        except Exception as e:
            logger.error(f"Error con spreadsheet: {e}")
            return False
            
    def export_trades(self, trades: List[Dict], worksheet_name: str = "Trades"):
        """Exporta trades a una hoja"""
        if not self.spreadsheet:
            return False
            
        try:
            # Crear o seleccionar worksheet
            try:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
                worksheet.clear()  # Limpiar contenido existente
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows=1000,
                    cols=20
                )
                
            if not trades:
                logger.warning("No hay trades para exportar")
                return False
                
            # Convertir a DataFrame
            df = pd.DataFrame(trades)
            
            # Ordenar columnas
            columns_order = [
                'ticket', 'symbol', 'trade_type', 'volume',
                'entry_price', 'exit_price', 'sl_price', 'tp_price',
                'entry_time', 'exit_time', 'profit_usd', 'profit_pips',
                'profit_percent', 'strategy', 'confidence', 'result'
            ]
            
            # Reordenar columnas existentes
            existing_cols = [col for col in columns_order if col in df.columns]
            df = df[existing_cols]
            
            # Convertir a lista de listas
            values = [df.columns.tolist()] + df.values.tolist()
            
            # Actualizar hoja
            worksheet.update('A1', values)
            
            # Formatear encabezados
            worksheet.format('A1:Z1', {
                'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            logger.info(f"Exportados {len(trades)} trades a Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando trades: {e}")
            return False
            
    def export_metrics(self, metrics: Dict, worksheet_name: str = "Metrics"):
        """Exporta métricas a una hoja"""
        if not self.spreadsheet:
            return False
            
        try:
            # Crear o seleccionar worksheet
            try:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows=100,
                    cols=10
                )
                
            # Preparar datos
            data = []
            data.append(['Métrica', 'Valor', 'Timestamp'])
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Métricas principales
            main_metrics = [
                ('Total Trades', metrics.get('total_trades', 0)),
                ('Win Rate', f"{metrics.get('win_rate', 0)*100:.2f}%"),
                ('Net Profit', f"${metrics.get('net_profit', 0):.2f}"),
                ('Profit Factor', f"{metrics.get('profit_factor', 0):.2f}"),
                ('Sharpe Ratio', f"{metrics.get('sharpe_ratio', 0):.2f}"),
                ('Sortino Ratio', f"{metrics.get('sortino_ratio', 0):.2f}"),
                ('Max Drawdown', f"${metrics.get('max_drawdown', 0):.2f}"),
                ('Max DD %', f"{metrics.get('max_drawdown_percent', 0):.2f}%"),
                ('VaR 95%', f"${metrics.get('var_95', 0):.2f}"),
                ('Calmar Ratio', f"{metrics.get('calmar_ratio', 0):.2f}"),
                ('Expectancy', f"${metrics.get('expectancy', 0):.2f}"),
                ('Recovery Factor', f"{metrics.get('recovery_factor', 0):.2f}"),
            ]
            
            for metric_name, metric_value in main_metrics:
                data.append([metric_name, metric_value, timestamp])
                
            # Separador
            data.append(['', '', ''])
            data.append(['Por Símbolo', '', ''])
            
            # Métricas por símbolo
            for symbol, symbol_metrics in metrics.get('by_symbol', {}).items():
                data.append([
                    f"  {symbol}",
                    f"${symbol_metrics['profit']:.2f} ({symbol_metrics['trades']} trades)",
                    f"WR: {symbol_metrics['win_rate']*100:.1f}%"
                ])
                
            # Separador
            data.append(['', '', ''])
            data.append(['Por Estrategia', '', ''])
            
            # Métricas por estrategia
            for strategy, strategy_metrics in metrics.get('by_strategy', {}).items():
                data.append([
                    f"  {strategy}",
                    f"${strategy_metrics['profit']:.2f} ({strategy_metrics['trades']} trades)",
                    f"WR: {strategy_metrics['win_rate']*100:.1f}%"
                ])
                
            # Actualizar hoja
            worksheet.update('A1', data)
            
            # Formatear
            worksheet.format('A1:C1', {
                'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.3},
                'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
            })
            
            logger.info("Métricas exportadas a Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando métricas: {e}")
            return False
            
    def export_daily_summary(self, balance: float, equity: float, trades_today: int, 
                            pnl_today: float, worksheet_name: str = "Daily_Summary"):
        """Exporta resumen diario a una hoja"""
        if not self.spreadsheet:
            return False
            
        try:
            # Crear o seleccionar worksheet
            try:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows=1000,
                    cols=10
                )
                # Añadir encabezados
                headers = ['Fecha', 'Hora', 'Balance', 'Equity', 'PnL Diario', 
                          'Trades Hoy', 'Floating PnL', 'DD%']
                worksheet.append_row(headers)
                
            # Preparar datos
            now = datetime.now()
            floating_pnl = equity - balance
            
            # Calcular DD% si hay historial
            last_rows = worksheet.get_all_values()
            if len(last_rows) > 1:
                max_equity = max(float(row[3]) for row in last_rows[1:] if row[3])
                dd_percent = ((max_equity - equity) / max_equity * 100) if max_equity > 0 else 0
            else:
                dd_percent = 0
                
            row_data = [
                now.strftime('%Y-%m-%d'),
                now.strftime('%H:%M:%S'),
                f"{balance:.2f}",
                f"{equity:.2f}",
                f"{pnl_today:.2f}",
                trades_today,
                f"{floating_pnl:.2f}",
                f"{dd_percent:.2f}"
            ]
            
            # Añadir fila
            worksheet.append_row(row_data)
            
            logger.info("Resumen diario exportado a Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Error exportando resumen diario: {e}")
            return False
            
    def create_dashboard_sheet(self):
        """Crea una hoja de dashboard con fórmulas"""
        if not self.spreadsheet:
            return False
            
        try:
            # Crear worksheet de dashboard
            try:
                worksheet = self.spreadsheet.worksheet("Dashboard")
                worksheet.clear()
            except gspread.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title="Dashboard",
                    rows=50,
                    cols=10
                )
                
            # Configurar dashboard con fórmulas
            dashboard_data = [
                ['ALGO TRADER V3 - DASHBOARD', '', '', ''],
                ['', '', '', ''],
                ['RESUMEN GENERAL', '', '', ''],
                ['Balance Actual:', '=INDIRECT("Daily_Summary!C"&COUNTA(Daily_Summary!C:C))', '', ''],
                ['Equity Actual:', '=INDIRECT("Daily_Summary!D"&COUNTA(Daily_Summary!D:D))', '', ''],
                ['PnL Total:', '=SUM(Trades!K:K)', '', ''],
                ['', '', '', ''],
                ['MÉTRICAS DE RENDIMIENTO', '', '', ''],
                ['Total Trades:', '=COUNTA(Trades!A:A)-1', '', ''],
                ['Win Rate:', '=COUNTIF(Trades!P:P,"WIN")/(COUNTA(Trades!P:P)-1)', '', ''],
                ['Profit Factor:', '=SUMIF(Trades!K:K,">0")/ABS(SUMIF(Trades!K:K,"<0"))', '', ''],
                ['Max Drawdown:', '=MIN(Daily_Summary!H:H)&"%"', '', ''],
                ['', '', '', ''],
                ['TOP SÍMBOLOS', '', '', ''],
                ['XAUUSD:', '=SUMIF(Trades!B:B,"XAUUSD",Trades!K:K)', '', ''],
                ['BTCUSD:', '=SUMIF(Trades!B:B,"BTCUSD",Trades!K:K)', '', ''],
                ['EURUSD:', '=SUMIF(Trades!B:B,"EURUSD",Trades!K:K)', '', ''],
                ['GBPUSD:', '=SUMIF(Trades!B:B,"GBPUSD",Trades!K:K)', '', ''],
            ]
            
            # Actualizar dashboard
            worksheet.update('A1', dashboard_data)
            
            # Formatear título
            worksheet.format('A1:D1', {
                'backgroundColor': {'red': 0.1, 'green': 0.3, 'blue': 0.7},
                'textFormat': {
                    'bold': True,
                    'fontSize': 14,
                    'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}
                },
                'horizontalAlignment': 'CENTER'
            })
            
            # Formatear secciones
            for row in [3, 8, 14]:
                worksheet.format(f'A{row}:D{row}', {
                    'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9},
                    'textFormat': {'bold': True}
                })
                
            logger.info("Dashboard creado en Google Sheets")
            return True
            
        except Exception as e:
            logger.error(f"Error creando dashboard: {e}")
            return False
            
    def get_spreadsheet_url(self) -> Optional[str]:
        """Obtiene la URL de la hoja de cálculo"""
        if self.spreadsheet:
            return self.spreadsheet.url
        return None


# Función auxiliar para configuración inicial
def setup_google_sheets_credentials():
    """Ayuda a configurar las credenciales de Google Sheets"""
    print("\n=== CONFIGURACIÓN DE GOOGLE SHEETS ===\n")
    print("Para usar Google Sheets necesitas:")
    print("1. Crear un proyecto en Google Cloud Console")
    print("2. Habilitar Google Sheets API")
    print("3. Crear credenciales de cuenta de servicio")
    print("4. Descargar el archivo JSON de credenciales")
    print("5. Guardarlo como 'configs/google_credentials.json'")
    print("\nGuía completa:")
    print("https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account")
    print("\nUna vez configurado, el sistema exportará automáticamente.")
    

if __name__ == "__main__":
    # Test del exportador
    
    if not GSPREAD_AVAILABLE:
        print("Instalando dependencias...")
        os.system("pip install gspread google-auth")
        print("\nReinicia el script después de la instalación.")
    else:
        # Verificar si existen credenciales
        creds_file = "configs/google_credentials.json"
        
        if not os.path.exists(creds_file):
            setup_google_sheets_credentials()
        else:
            # Test de exportación
            exporter = GoogleSheetsExporter(creds_file)
            
            if exporter.client:
                # Crear o abrir spreadsheet
                if exporter.create_or_open_spreadsheet("AlgoTrader_Test"):
                    
                    # Datos de prueba
                    test_trade = {
                        'ticket': 12345,
                        'symbol': 'XAUUSD',
                        'trade_type': 'BUY',
                        'volume': 0.01,
                        'entry_price': 2650.50,
                        'exit_price': 2655.00,
                        'sl_price': 2648.00,
                        'tp_price': 2655.00,
                        'entry_time': datetime.now().isoformat(),
                        'exit_time': datetime.now().isoformat(),
                        'profit_usd': 45.0,
                        'profit_pips': 45,
                        'profit_percent': 0.17,
                        'strategy': 'AI_Hybrid',
                        'confidence': 0.85,
                        'result': 'WIN'
                    }
                    
                    test_metrics = {
                        'total_trades': 100,
                        'win_rate': 0.65,
                        'net_profit': 1250.50,
                        'profit_factor': 1.8,
                        'sharpe_ratio': 1.25,
                        'sortino_ratio': 1.45,
                        'max_drawdown': 250.00,
                        'max_drawdown_percent': 2.5,
                        'var_95': -50.00,
                        'calmar_ratio': 2.1,
                        'expectancy': 12.50,
                        'recovery_factor': 5.0,
                        'by_symbol': {
                            'XAUUSD': {'trades': 40, 'profit': 500, 'win_rate': 0.7},
                            'BTCUSD': {'trades': 30, 'profit': 450, 'win_rate': 0.6}
                        },
                        'by_strategy': {
                            'AI_Hybrid': {'trades': 50, 'profit': 700, 'win_rate': 0.68},
                            'Multi_TF': {'trades': 50, 'profit': 550.5, 'win_rate': 0.62}
                        }
                    }
                    
                    # Exportar datos de prueba
                    print("\nExportando trades...")
                    exporter.export_trades([test_trade])
                    
                    print("Exportando métricas...")
                    exporter.export_metrics(test_metrics)
                    
                    print("Exportando resumen diario...")
                    exporter.export_daily_summary(10000, 10250, 5, 250)
                    
                    print("Creando dashboard...")
                    exporter.create_dashboard_sheet()
                    
                    print(f"\n✅ Exportación completa!")
                    print(f"📊 Ver en: {exporter.get_spreadsheet_url()}")
                else:
                    print("Error creando/abriendo spreadsheet")
            else:
                print("No se pudo inicializar el cliente de Google Sheets")
                setup_google_sheets_credentials()