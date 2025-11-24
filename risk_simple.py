
class RiskManagerSimple:
    def __init__(self, capital=10000):
        self.capital = capital
        self.max_risk = 0.02
        
    def calculate_position_size(self, entry_price, stop_loss):
        risk_amount = self.capital * self.max_risk
        price_risk = abs(entry_price - stop_loss)
        
        if price_risk > 0:
            # Para forex: size en lotes
            size = (risk_amount / price_risk) / 100000
            return min(5.0, max(0.01, size))
        return 0.01
        
    def check_limits(self):
        return {'can_trade': True, 'warnings': [], 'blocks': []}
