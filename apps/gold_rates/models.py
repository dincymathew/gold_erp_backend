from django.db import models

class Rate(models.Model):
    gold_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.0) # Market price per unit
    forex_rate = models.DecimalField(max_digits=10, decimal_places=2, default=1.0) # USD to UGX
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Gold: {self.gold_price}, Forex: {self.forex_rate}"

    @classmethod
    def get_current(cls):
        rate = cls.objects.first()
        if not rate:
            rate = cls.objects.create(gold_price=2000.0, forex_rate=3800.0)
        return rate
