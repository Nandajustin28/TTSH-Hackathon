#!/usr/bin/env python3
"""
Test script to check dashboard statistics calculation
Run this to verify that the dashboard calculations match the database
"""

import sqlite3
import os

# Change to the project directory
os.chdir('/Users/nanda28/Desktop/TTSH2')

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

print("=== Dashboard Statistics Test ===\n")

# Test 1: Total forms
cursor.execute("SELECT COUNT(*) FROM dashboard_patientform")
total_forms = cursor.fetchone()[0]
print(f"Total forms in database: {total_forms}")

# Test 2: Approved forms
cursor.execute("SELECT COUNT(*) FROM dashboard_patientform WHERE status='approved'")
approved_forms = cursor.fetchone()[0]
print(f"Approved forms: {approved_forms}")

# Test 3: Rejected forms
cursor.execute("SELECT COUNT(*) FROM dashboard_patientform WHERE status='rejected'")
rejected_forms = cursor.fetchone()[0]
print(f"Rejected forms: {rejected_forms}")

# Test 4: Pending forms
cursor.execute("SELECT COUNT(*) FROM dashboard_patientform WHERE status='pending'")
pending_forms = cursor.fetchone()[0]
print(f"Pending forms: {pending_forms}")

# Test 5: Processing forms
cursor.execute("SELECT COUNT(*) FROM dashboard_patientform WHERE status='processing'")
processing_forms = cursor.fetchone()[0]
print(f"Processing forms: {processing_forms}")

# Test 6: Forms with processing times
cursor.execute("SELECT COUNT(*) FROM dashboard_patientform WHERE processing_time_seconds IS NOT NULL")
forms_with_times = cursor.fetchone()[0]
print(f"Forms with processing times: {forms_with_times}")

# Test 7: Average processing time
cursor.execute("SELECT AVG(processing_time_seconds) FROM dashboard_patientform WHERE processing_time_seconds IS NOT NULL")
result = cursor.fetchone()[0]
if result:
    avg_time_seconds = result
    avg_minutes = round(avg_time_seconds / 60, 1)
    print(f"Average processing time: {avg_time_seconds}s ({avg_minutes}m)")
else:
    print("Average processing time: No data available")

# Test 8: Acceptance rate
processed_total = approved_forms + rejected_forms
if processed_total > 0:
    acceptance_rate = round((approved_forms / processed_total) * 100)
    print(f"Acceptance rate: {acceptance_rate}% ({approved_forms}/{processed_total})")
else:
    print("Acceptance rate: 0% (no processed forms)")

# Test 9: Recent forms
print(f"\n=== Recent Forms ===")
cursor.execute("""
    SELECT id, patient_name, extracted_patient_name, status, ai_decision, uploaded_at 
    FROM dashboard_patientform 
    ORDER BY uploaded_at DESC 
    LIMIT 5
""")
recent_forms = cursor.fetchall()

for form in recent_forms:
    form_id, patient_name, extracted_name, status, ai_decision, uploaded_at = form
    display_name = patient_name or extracted_name or "Unknown"
    print(f"ID: {form_id}, Patient: {display_name}, Status: {status}, AI: {ai_decision}, Date: {uploaded_at}")

conn.close()

print(f"\n=== Expected Dashboard Values ===")
print(f"Total Forms: {total_forms}")
print(f"Accepted: {approved_forms}")  
print(f"Rejected: {rejected_forms}")
print(f"Average Processing Time: {avg_minutes if 'avg_minutes' in locals() else '0.0'}m")
if processed_total > 0:
    print(f"Acceptance Rate: {acceptance_rate}%")
else:
    print(f"Acceptance Rate: 0%")