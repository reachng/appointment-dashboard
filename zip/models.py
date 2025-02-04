from django.db import models

class Location(models.Model):
    country = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    
    def __str__(self):
        return f"{self.country} - {self.district} - {self.zip_code}"


class Address(models.Model):
    address_id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    county = models.CharField(max_length=255)
    state = models.CharField(max_length=200)
    zip = models.CharField(max_length=1000)
    status = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.county}, {self.state} ({self.zip})"
        

class Address_mapped(models.Model):
    address_id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField(null=True, blank=True)  # User ID may be optional
    county = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=20)
    zip = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10)
    latitude = models.FloatField(null=True, blank=True)  # Latitude may be optional
    longitude = models.FloatField(null=True, blank=True)  # Longitude may be optional

    def __str__(self):
        return f"{self.county}, {self.state} ({self.zip})"

class User(models.Model):
    user_id = models.IntegerField(primary_key=True)
    hear_from = models.CharField(max_length=255, null=True, blank=True)  # Could be a string or null
    status = models.CharField(max_length=10, null=True, blank=True)  # P, A, etc.
    cdate = models.DateTimeField(null=True, blank=True)  # Created date
    mdate = models.DateTimeField(null=True, blank=True)  # Modified date
    zip = models.CharField(max_length=100, null=True, blank=True)  # Zip code as string
    register_from = models.CharField(max_length=10, null=True, blank=True)  # A, etc.
    referral_url = models.URLField(max_length=500, null=True, blank=True)
    influencer = models.CharField(max_length=255, null=True, blank=True)  # Optional
    apple_profile_id = models.CharField(max_length=255, null=True, blank=True)  # Optional

    def __str__(self):
        return f"User {self.user_id}"

class Appointment(models.Model):
    appointment_id = models.IntegerField(primary_key=True)
    user_id = models.IntegerField()
    address_id = models.IntegerField()
    payment_id = models.IntegerField(null=True, blank=True)
    g_id = models.IntegerField(null=True, blank=True)
    g_assigned_by = models.CharField(max_length=100, null=True, blank=True)  # G or S
    sub_total = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    promo_amt = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    credit_amt = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    new_credit = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    safety_insurance = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    sameday_booking = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    tax = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    surcharge_amt = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    total_final = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    tip = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    tip_surcharge_amt = models.DecimalField(max_digits=100, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)  # C, L, etc.
    reserved_at = models.CharField(max_length=255, null=True, blank=True)  # Time range as string
    reserved_date = models.CharField(max_length=255, null=True, blank=True)
    cdate = models.DateTimeField(null=True, blank=True)  # Created at
    accepted_date = models.DateTimeField(null=True, blank=True)
    g_confirm_date = models.DateTimeField(null=True, blank=True)
    rating = models.FloatField(null=True, blank=True)
    mdate = models.DateTimeField(null=True, blank=True)
    if_complain = models.CharField(max_length=3, null=True, blank=True)  # Yes/No
    delayed = models.CharField(max_length=100, null=True, blank=True)  # Y/N
    ontheway_eta = models.CharField(max_length=50, null=True, blank=True)  # Time as string
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    cancel_date = models.DateTimeField(null=True, blank=True)
    order_from = models.CharField(max_length=100, null=True, blank=True)  # A, L, etc.
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Appointment {self.appointment_id}"