from django.db import models

class Branch(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    x_factor = models.DecimalField(max_digits=12, decimal_places=4, default=92.0000)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_branches')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (X: {self.x_factor})"

class UOM(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    type = models.CharField(max_length=255, choices=[
        ('smaller', 'Smaller than reference'),
        ('reference', 'Reference Unit'),
        ('bigger', 'Bigger than reference')
    ])

    def __str__(self):
        return f"{self.name} ({self.code})"

class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.code

class Expense(models.Model):
    CATEGORY_CHOICES = (
        ('GOLD_PURCHASE', 'Gold Purchase'),
        ('BRANCH_EXPENSE', 'Branch Expense'),
        ('OTHER', 'Other Expense'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='GOLD_PURCHASE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    source_name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_expenses')
    rate_per_gram = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    grams = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.category}] {self.source_name} - {self.total}"
