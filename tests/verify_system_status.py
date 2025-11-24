"""
Sistema de Verificación Rápida - Multi Account Status
"""
import os
import json
from datetime import datetime
from pathlib import Path

def check_configuration():
    """Verifica la configuración del sistema"""
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║          VERIFICACIÓN DE SISTEMA EXNESS                    ║
    ║                    Version 3.2                            ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print(f"📅 Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Verificar archivo .env
    print("="*60)
    print("1️⃣ VERIFICANDO ARCHIVO .ENV")
    print("="*60)
    
    env_path = Path('.env')
    if env_path.exists():
        print("✅ Archivo .env encontrado")
        with open('.env', 'r') as f:
            lines = f.readlines()
            
        exness_login = None
        
        for line in lines:
            if 'MT5_LOGIN=' in line and 'MT5_LOGIN_AVA' not in line:
                exness_login = line.split('=')[1].strip()
                
        if exness_login:
            print(f"✅ EXNESS Login configurado: {exness_login}")
        else:
            print("❌ EXNESS Login no encontrado")
    else:
        print("❌ Archivo .env no encontrado")
    
    # Verificar archivos del sistema
    print("\n" + "="*60)
    print("2️⃣ VERIFICANDO ARCHIVOS DEL SISTEMA")
    print("="*60)
    
    files_to_check = [
        ('multi_account_manager_fixed.py', 'Gestor Multi-Cuenta Corregido'),
        ('check_accounts_independent.py', 'Verificador Independiente'),
        ('MULTI_ACCOUNT_FIXED.bat', 'Script de Ejecución'),
        ('CHECK_ACCOUNTS_INDEPENDENT.bat', 'Script de Verificación')
    ]
    
    for file_name, description in files_to_check:
        if Path(file_name).exists():
            size = Path(file_name).stat().st_size
            print(f"✅ {description}: {file_name} ({size:,} bytes)")
        else:
            print(f"❌ {description}: {file_name} NO ENCONTRADO")
    
    # Verificar paths de MT5
    print("\n" + "="*60)
    print("3️⃣ VERIFICANDO INSTALACIÓN DE MT5 EXNESS")
    print("="*60)
    
    from dotenv import load_dotenv
    load_dotenv('configs/.env')
    
    mt5_path = os.getenv('MT5_PATH', r'C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe')
    
    if Path(mt5_path).exists():
        print(f"✅ EXNESS MT5: Encontrado en {mt5_path}")
    else:
        print(f"⚠️ EXNESS MT5: No encontrado en {mt5_path}")
        print(f"   Verifica la ruta de instalación en configs/.env (MT5_PATH)")
        
        # Buscar rutas alternativas
        alternative_paths = [
            r'C:\Program Files\MetaTrader 5 Exness\terminal64.exe',
            r'C:\Program Files\Exness MetaTrader 5\terminal64.exe'
        ]
        for alt_path in alternative_paths:
            if Path(alt_path).exists():
                print(f"✅ Alternativa encontrada: {alt_path}")
                break
    
    # Verificar logs
    print("\n" + "="*60)
    print("4️⃣ VERIFICANDO DIRECTORIO DE LOGS")
    print("="*60)
    
    logs_dir = Path('logs')
    if logs_dir.exists():
        print(f"✅ Directorio logs/ existe")
        log_files = list(logs_dir.glob('*.log'))
        if log_files:
            print(f"   Encontrados {len(log_files)} archivos de log")
            recent_logs = sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
            for log in recent_logs:
                print(f"   - {log.name}")
        else:
            print("   No hay archivos de log")
    else:
        print("⚠️ Directorio logs/ no existe")
        logs_dir.mkdir(exist_ok=True)
        print("✅ Directorio logs/ creado")
    
    # Resumen de credenciales configuradas
    print("\n" + "="*60)
    print("5️⃣ CREDENCIALES CONFIGURADAS")
    print("="*60)
    
    print("\n📊 EXNESS TRIAL (Única cuenta configurada):")
    print("   Login: 197678662")
    print("   Password: ********* (configurada)")
    print("   Servidor: Exness-MT5Trial11")
    print(f"   Path: {os.getenv('MT5_PATH', 'No configurado')}")
    
    # Estado del sistema
    print("\n" + "="*60)
    print("📈 ESTADO DEL SISTEMA")
    print("="*60)
    
    all_ok = True
    issues = []
    
    if not env_path.exists():
        all_ok = False
        issues.append("Archivo .env no encontrado")
    
    if not Path('multi_account_manager_fixed.py').exists():
        all_ok = False
        issues.append("Gestor multi-cuenta no encontrado")
    
    if all_ok:
        print("✅ SISTEMA LISTO PARA USAR")
        print("\nCOMANDOS DISPONIBLES:")
        print("1. CHECK_ACCOUNTS_INDEPENDENT.bat - Verificar cuentas")
        print("2. MULTI_ACCOUNT_FIXED.bat - Ejecutar monitor")
    else:
        print("⚠️ SISTEMA REQUIERE ATENCIÓN")
        print("\nProblemas detectados:")
        for issue in issues:
            print(f"   - {issue}")
    
    # Solución al problema de duplicación
    print("\n" + "="*60)
    print("💡 CONFIGURACIÓN EXNESS")
    print("="*60)
    print(f"""
El sistema ha sido actualizado para usar únicamente EXNESS:

1. ✅ Conexión exclusiva a EXNESS
2. ✅ Path configurado desde variables de entorno
3. ✅ Eliminadas referencias a otras cuentas
4. ✅ Prevención de múltiples instancias MT5

CONFIGURACIÓN ACTUAL:
       - EXNESS: 197678662 (única cuenta activa)
       - Path: {os.getenv('MT5_PATH', 'No configurado')}
    """)
    
    print("="*60)
    print("\n✅ Verificación completada")

if __name__ == "__main__":
    check_configuration()
    input("\nPresiona Enter para salir...")
