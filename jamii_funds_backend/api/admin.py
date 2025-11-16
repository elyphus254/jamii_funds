# admin.py
from django.contrib import admin
from .models import Chama, Member, Membership, Contribution, Loan, Repayment

@admin.register(Chama)
class ChamaAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_contributions', 'total_loans_outstanding', 'is_active')
    search_fields = ('name',)

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'is_active')
    search_fields = ('name', 'phone', 'national_id')

# NEW: Membership Admin with Inlines
class ContributionInline(admin.TabularInline):
    model = Contribution
    extra = 1
    fields = ('amount', 'date', 'confirmed', 'transaction_ref')
    readonly_fields = ('date',)

class LoanInline(admin.TabularInline):
    model = Loan
    extra = 0
    fields = ('principal', 'status', 'applied_at', 'approved_at', 'emi')
    readonly_fields = ('applied_at', 'approved_at', 'emi')

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('member', 'chama', 'joined_at', 'is_admin', 'is_active')
    list_filter = ('chama', 'is_admin', 'is_active')
    search_fields = ('member__name', 'member__phone', 'chama__name')
    inlines = [ContributionInline, LoanInline]