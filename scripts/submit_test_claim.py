import httpx, base64, time
FAST='http://localhost:8000'
emp='EMP-001'

def get_budget():
    r=httpx.get(f'{FAST}/employees/{emp}/budget', timeout=30)
    print('BUDGET STATUS:', r.status_code)
    try:
        j=r.json()
        print('Current month spend:', j.get('current_month_spend'))
        print('Remaining:', j.get('remaining'))
    except Exception as e:
        print('Error parsing budget response', e, r.text[:200])

print('--- Budget BEFORE submission ---')
get_budget()

# small 1x1 PNG
png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII=')

data={'employee_id':emp, 'employee_name':'Alice Chen','employee_email':'alice.chen@acmecorp.com','city':'London','city_tier':'A','category':'Meals','claimed_amount':'15.50','original_currency':'GBP','business_purpose':'Team lunch'}
files={'receipt':('test.png', png, 'image/png')}

print('\nSubmitting claim...')
try:
    r=httpx.post(f'{FAST}/claims/submit', data=data, files=files, timeout=60)
    print('Submit status:', r.status_code)
    print('Submit response:', r.text[:300])
    claim_id = r.json().get('claim_id')
except Exception as e:
    print('Submit failed:', e)
    claim_id = None

# wait a few seconds for quick OCR seed/background tasks
time.sleep(3)
print('\n--- Budget AFTER submission (immediate) ---')
get_budget()

if claim_id:
    print('\nSubmitted Claim ID:', claim_id)
    print('You can view it in the app under My Previous Claims or the Claim Audit Report.')
