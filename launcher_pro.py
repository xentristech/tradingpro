"""
Final Verification and Launch Script
Complete system verification and interactive launcher
"""
import os
import sys
import time
from datetime import datetime
from pathlib import Path
import json

# Add colors for better visibility
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    """Print application header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}")
    print("="*70)
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║      ENHANCED ALGORITHMIC TRADING BOT v2.0               ║
    ║           Professional Grade Trading System              ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    print("="*70)
    print(f"{Colors.RESET}")

def check_system_status():
    """Check overall system status"""
    print(f"\n{Colors.YELLOW}🔍 SYSTEM STATUS CHECK{Colors.RESET}")
    print("-"*50)
    
    checks = {
        'Python Environment': check_python_env(),
        'Core Modules': check_core_modules(),
        'Enhanced Modules': check_enhanced_modules(),
        'Configuration': check_configuration(),
        'Directories': check_directories()
    }
    
    all_pass = all(checks.values())
    
    for component, status in checks.items():
        icon = "✅" if status else "❌"
        color = Colors.GREEN if status else Colors.RED
        print(f"{color}  {icon} {component}{Colors.RESET}")
    
    return all_pass

def check_python_env():
    """Check Python environment"""
    try:
        version = sys.version_info
        return version.major == 3 and version.minor >= 8
    except:
        return False

def check_core_modules():
    """Check core Python modules"""
    required = ['pandas', 'numpy', 'requests', 'yaml']
    try:
        for module in required:
            __import__(module)
        return True
    except:
        return False

def check_enhanced_modules():
    """Check enhanced trading modules"""
    modules = [
        'risk.advanced_risk',
        'data.advanced_indicators',
        'ml.trading_models',
        'backtesting.advanced_backtest'
    ]
    try:
        for module in modules:
            exec(f"from {module} import *")
        return True
    except:
        return False

def check_configuration():
    """Check configuration files"""
    files = ['configs/.env', 'configs/settings.yaml']
    return all(Path(f).exists() for f in files)

def check_directories():
    """Check required directories"""
    dirs = ['logs', 'data', 'ml/models', 'backtesting/results']
    return all(Path(d).exists() for d in dirs)

def display_menu():
    """Display interactive menu"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}📋 MAIN MENU{Colors.RESET}")
    print("-"*50)
    print(f"{Colors.GREEN}1.{Colors.RESET} 🚀 Run Trading Bot (Live/Demo)")
    print(f"{Colors.GREEN}2.{Colors.RESET} 🧠 Train Machine Learning Models")
    print(f"{Colors.GREEN}3.{Colors.RESET} 📊 Run Backtest Analysis")
    print(f"{Colors.GREEN}4.{Colors.RESET} 🎭 Run System Demo")
    print(f"{Colors.GREEN}5.{Colors.RESET} 🔍 System Health Check")
    print(f"{Colors.GREEN}6.{Colors.RESET} 📈 View Performance Stats")
    print(f"{Colors.GREEN}7.{Colors.RESET} ⚙️  Configuration Settings")
    print(f"{Colors.GREEN}8.{Colors.RESET} 📚 View Documentation")
    print(f"{Colors.GREEN}9.{Colors.RESET} 🔄 Update Dependencies")
    print(f"{Colors.GREEN}0.{Colors.RESET} ❌ Exit")
    print("-"*50)

def run_trading_bot():
    """Launch trading bot"""
    print(f"\n{Colors.CYAN}🚀 LAUNCHING TRADING BOT...{Colors.RESET}")
    
    # Check if live trading
    from dotenv import load_dotenv
    load_dotenv('configs/.env')
    is_live = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
    
    mode = "LIVE" if is_live else "DEMO"
    color = Colors.RED if is_live else Colors.GREEN
    
    print(f"\n{color}{'='*50}")
    print(f"  TRADING MODE: {mode}")
    print(f"{'='*50}{Colors.RESET}")
    
    if is_live:
        print(f"\n{Colors.YELLOW}⚠️  WARNING: LIVE TRADING ENABLED!{Colors.RESET}")
        confirm = input("Are you sure you want to continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
    
    try:
        from enhanced_trading_bot import EnhancedTradingBot
        bot = EnhancedTradingBot()
        bot.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Bot stopped by user.{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")

def train_ml_models():
    """Train ML models"""
    print(f"\n{Colors.CYAN}🧠 TRAINING MACHINE LEARNING MODELS...{Colors.RESET}")
    try:
        from enhanced_trading_bot import EnhancedTradingBot
        bot = EnhancedTradingBot()
        bot.train_models()
        print(f"\n{Colors.GREEN}✅ Models trained successfully!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")

def run_backtest():
    """Run backtesting"""
    print(f"\n{Colors.CYAN}📊 RUNNING BACKTEST ANALYSIS...{Colors.RESET}")
    try:
        from enhanced_trading_bot import EnhancedTradingBot
        bot = EnhancedTradingBot()
        bot.run_backtest()
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")

def run_demo():
    """Run system demo"""
    print(f"\n{Colors.CYAN}🎭 RUNNING SYSTEM DEMO...{Colors.RESET}")
    try:
        os.system('python demo_enhanced_bot.py')
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")

def system_health_check():
    """Perform system health check"""
    print(f"\n{Colors.CYAN}🔍 SYSTEM HEALTH CHECK...{Colors.RESET}")
    try:
        os.system('python system_check.py')
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")

def view_performance():
    """View performance statistics"""
    print(f"\n{Colors.CYAN}📈 PERFORMANCE STATISTICS{Colors.RESET}")
    print("-"*50)
    
    # Try to load latest backtest results
    try:
        if Path('demo_results.json').exists():
            with open('demo_results.json', 'r') as f:
                results = json.load(f)
            
            print(f"\n{Colors.GREEN}Latest Results:{Colors.RESET}")
            print(f"  Timestamp: {results.get('timestamp', 'N/A')}")
            print(f"  Status: {results.get('status', 'N/A')}")
            print(f"  Performance: {results.get('performance_improvement', 'N/A')}")
            
            if 'signal' in results:
                signal = results['signal']
                print(f"\n{Colors.YELLOW}Last Signal:{Colors.RESET}")
                print(f"  Action: {signal.get('action', 'N/A')}")
                print(f"  Confidence: {signal.get('confidence', 0)*100:.1f}%")
                print(f"  Price: ${signal.get('price', 0):,.2f}")
        else:
            print("No performance data available. Run demo or backtest first.")
    except Exception as e:
        print(f"{Colors.RED}Error loading performance data: {e}{Colors.RESET}")

def view_configuration():
    """View and edit configuration"""
    print(f"\n{Colors.CYAN}⚙️  CONFIGURATION SETTINGS{Colors.RESET}")
    print("-"*50)
    
    from dotenv import load_dotenv
    load_dotenv('configs/.env')
    
    config = {
        'Symbol': os.getenv('SYMBOL', 'Not set'),
        'Live Trading': os.getenv('LIVE_TRADING', 'false'),
        'Risk per Trade': '2%',
        'Max Drawdown': '10%',
        'API Keys': {
            'TwelveData': 'Set' if os.getenv('TWELVEDATA_API_KEY') else 'Not set',
            'Telegram': 'Set' if os.getenv('TELEGRAM_TOKEN') else 'Not set',
            'MT5': 'Set' if os.getenv('MT5_LOGIN') else 'Not set'
        }
    }
    
    print(f"\n{Colors.GREEN}Current Configuration:{Colors.RESET}")
    for key, value in config.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                color = Colors.GREEN if v != 'Not set' else Colors.RED
                print(f"    {color}{k}: {v}{Colors.RESET}")
        else:
            print(f"  {key}: {value}")
    
    print(f"\n{Colors.YELLOW}To edit: modify configs/.env{Colors.RESET}")

def view_documentation():
    """View documentation"""
    print(f"\n{Colors.CYAN}📚 DOCUMENTATION{Colors.RESET}")
    print("-"*50)
    
    docs = {
        '1': ('Quick Start Guide', 'QUICK_START.md'),
        '2': ('Complete Documentation', 'README_COMPLETO.md'),
        '3': ('Final Report', 'INFORME_FINAL.md')
    }
    
    print("\nAvailable Documentation:")
    for key, (name, file) in docs.items():
        exists = "✅" if Path(file).exists() else "❌"
        print(f"  {key}. {exists} {name}")
    
    choice = input("\nSelect document to view (1-3) or 0 to cancel: ")
    
    if choice in docs:
        file = docs[choice][1]
        if Path(file).exists():
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"\n{Colors.CYAN}{'-'*70}{Colors.RESET}")
                print(content[:2000] + "...")  # Show first 2000 chars
                print(f"\n{Colors.YELLOW}Full document: {file}{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}Error reading file: {e}{Colors.RESET}")

def update_dependencies():
    """Update Python dependencies"""
    print(f"\n{Colors.CYAN}🔄 UPDATING DEPENDENCIES...{Colors.RESET}")
    try:
        os.system('pip install -r requirements.txt --upgrade')
        print(f"\n{Colors.GREEN}✅ Dependencies updated!{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")

def main():
    """Main application loop"""
    print_header()
    
    # Initial system check
    if not check_system_status():
        print(f"\n{Colors.RED}⚠️  System check failed!{Colors.RESET}")
        print("Please run: python setup.py")
        input("\nPress Enter to continue anyway...")
    else:
        print(f"\n{Colors.GREEN}✅ All systems operational!{Colors.RESET}")
    
    # Main menu loop
    while True:
        display_menu()
        
        choice = input(f"\n{Colors.YELLOW}Select option (0-9): {Colors.RESET}")
        
        actions = {
            '1': run_trading_bot,
            '2': train_ml_models,
            '3': run_backtest,
            '4': run_demo,
            '5': system_health_check,
            '6': view_performance,
            '7': view_configuration,
            '8': view_documentation,
            '9': update_dependencies
        }
        
        if choice == '0':
            print(f"\n{Colors.CYAN}👋 Goodbye! Happy trading!{Colors.RESET}")
            break
        elif choice in actions:
            try:
                actions[choice]()
                input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}Error: {e}{Colors.RESET}")
                input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.RESET}")
        else:
            print(f"{Colors.RED}Invalid option!{Colors.RESET}")
    
    # Save session info
    session_info = {
        'timestamp': datetime.now().isoformat(),
        'session_duration': 'N/A',
        'actions_performed': 'N/A'
    }
    
    with open('last_session.json', 'w') as f:
        json.dump(session_info, f, indent=2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Program interrupted by user.{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
    finally:
        print(f"\n{Colors.CYAN}Session ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
