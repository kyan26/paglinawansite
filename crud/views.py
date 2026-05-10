from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from .models import Genders, Users
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator
from django.http import JsonResponse
import json

# Create your views here.

def gender_list(request):
    try:
        genders = Genders.objects.all()
        data = {
            'genders': genders
        }
        return render(request, 'gender/GendersList.html', data)
    except Exception as e:
        return HttpResponse(f'Error occured during load genders: {e}')

def add_gender(request):
    try:
        if request.method == 'POST':
            gender = request.POST.get('gender')
            Genders.objects.create(gender=gender).save()
            messages.success(request, 'Gender added successfully!')
            return redirect('/gender/list')
        else:
            return render(request, 'gender/AddGender.html')
    except Exception as e:
        return HttpResponse(f'Error occured during add gender {e}')

def edit_gender(request, genderId):
    try:
        if request.method == 'POST':
            genderObj = Genders.objects.get(pk=genderId)
            gender = request.POST.get('gender')
            genderObj.gender = gender
            genderObj.save()
            messages.success(request, 'Gender updated successfully!')
            data = {
                'gender': genderObj
            }
            return render(request, 'gender/EditGender.html', data)
        else:
            genderObj = Genders.objects.get(pk=genderId)
        data = {
            'gender': genderObj
        }
        return render(request, 'gender/EditGender.html', data)
    except Exception as e:
        return HttpResponse(f'Error occured during edit gender: {e}')

def delete_gender(request, genderId):
    try:
        if request.method == 'POST':
            genderObj = Genders.objects.get(pk=genderId)
            genderObj.delete()
            messages.success(request, 'Gender deleted successfully!')
            return redirect('/gender/list')
        else:
            genderObj = Genders.objects.get(pk=genderId)
        data = {
            'gender': genderObj
        }
        return render(request, 'gender/DeleteGender.html', data)
    except Exception as e:
        return HttpResponse(f'Error occured during delete gender: {e}')

def user_list(request):
    try:
        search = request.GET.get('search')

        userObj = Users.objects.select_related('gender').order_by('-user_id')

        if search:
            userObj = userObj.filter(
                Q(full_name__icontains=search) |
                Q(username__icontains=search) |
                Q(address__icontains=search) |
                Q(contact_number__icontains=search) |
                Q(gender__gender__icontains=search) |
                Q(birth_date__icontains=search) |
                Q(email__icontains=search)
            )

        paginator = Paginator(userObj, 10)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        data = {
            'users': page_obj,
            'search': search,
            'page_obj': page_obj,
        }

        return render(request, 'user/UsersList.html', data)

    except Exception as e:
        return HttpResponse(f'Error occured during load users {e}')

def add_user(request):
    try:
        if request.method == 'POST':
            fullName = request.POST.get('full_name', '').strip()
            gender = request.POST.get('gender', '').strip()
            birthDate = request.POST.get('birth_date', '').strip()
            address = request.POST.get('address', '').strip()
            contactNumber = request.POST.get('contact_number', '').strip()
            email = request.POST.get('email', '').strip()
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '')
            confirmPassword = request.POST.get('confirm_password', '')
            profilePicture = request.FILES.get('profile_picture')

            # ── Server-side validation ──────────────────────────────
            import re
            from datetime import date

            errors = []

            # Full name
            if not fullName:
                errors.append('Full name is required.')
            elif len(fullName) < 2:
                errors.append('Full name must be at least 2 characters.')
            elif re.search(r'[^a-zA-Z\s]', fullName):
                errors.append('Full name must contain letters only.')

            # Gender
            if not gender:
                errors.append('Please select a gender.')
            elif not Genders.objects.filter(pk=gender).exists():
                errors.append('Selected gender is invalid.')

            # Birth date
            if not birthDate:
                errors.append('Birth date is required.')
            else:
                try:
                    from datetime import datetime
                    birth = datetime.strptime(birthDate, '%Y-%m-%d').date()
                    today = date.today()
                    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                    if birth >= today:
                        errors.append('Birth date cannot be today or in the future.')
                    elif age > 120:
                        errors.append('Please enter a valid birth date.')
                    elif age < 5:
                        errors.append('Age seems too young.')
                except ValueError:
                    errors.append('Birth date format is invalid.')

            # Address
            if not address:
                errors.append('Address is required.')
            elif len(address) < 5:
                errors.append('Address must be at least 5 characters.')

            # Contact number
            if not contactNumber:
                errors.append('Contact number is required.')
            elif not re.fullmatch(r'\d+', contactNumber):
                errors.append('Contact number must contain numbers only.')
            elif contactNumber.startswith('09') and len(contactNumber) != 11:
                errors.append('Contact number starting with 09 must be 11 digits.')
            elif contactNumber.startswith('63') and len(contactNumber) != 12:
                errors.append('Contact number starting with 63 must be 12 digits.')
            elif not (contactNumber.startswith('09') or contactNumber.startswith('63')):
                errors.append('Contact number must start with 09 or 63.')

            # Username
            if not username:
                errors.append('Username is required.')
            elif len(username) < 3:
                errors.append('Username must be at least 3 characters.')
            elif re.search(r'\s', username):
                errors.append('Username cannot contain spaces.')
            elif re.search(r'[^a-zA-Z0-9_]', username):
                errors.append('Username may only contain letters, numbers, and underscores.')
            elif Users.objects.filter(username__iexact=username).exists():
                errors.append('Username already exists.')

            # Password
            if not password:
                errors.append('Password is required.')
            elif len(password) < 8:
                errors.append('Password must be at least 8 characters.')
            elif not re.search(r'[A-Z]', password):
                errors.append('Password must contain at least one uppercase letter.')
            elif not re.search(r'[0-9]', password):
                errors.append('Password must contain at least one number.')

            # Confirm password
            if password != confirmPassword:
                errors.append('Passwords do not match.')

            # Email (optional but must be valid if provided)
            if email:
                if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
                    errors.append('Please enter a valid email address.')

            # ── If any errors, stop and show them ──────────────────
            if errors:
                for error in errors:
                    messages.error(request, error)
                genderObj = Genders.objects.all()
                return render(request, 'user/AddUser.html', {'genders': genderObj})

            # ── Save ───────────────────────────────────────────────
            Users.objects.create(
                full_name=fullName,
                gender=Genders.objects.get(pk=gender),
                birth_date=birthDate,
                address=address,
                contact_number=contactNumber,
                email=email,
                username=username,
                password=make_password(password),
                profile_picture=profilePicture
            )

            messages.success(request, 'User added successfully!')
            return redirect('/user/add')

        else:
            genderObj = Genders.objects.all()

        data = {'genders': genderObj}
        return render(request, 'user/AddUser.html', data)

    except Exception as e:
        return HttpResponse(f'Error occurred during add user: {e}')

def user_delete(request, user_id):
    try:
        user = Users.objects.get(user_id=user_id)
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('/user/list')       # 👈 fixed

    except Users.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('/user/list')       # 👈 fixed

    except Exception as e:
        messages.error(request, f'Error occurred during delete: {e}')
        return redirect('/user/list')       # 👈 fixed

def user_edit(request, user_id):
    try:
        user = Users.objects.get(user_id=user_id)
        if request.method == 'POST':

            import re
            from datetime import date, datetime

            fullName = request.POST.get('full_name', '').strip()
            gender = request.POST.get('gender', '').strip()
            birthDate = request.POST.get('birth_date', '').strip()
            address = request.POST.get('address', '').strip()
            contactNumber = request.POST.get('contact_number', '').strip()
            email = request.POST.get('email', '').strip()

            errors = []

            # Full name
            if not fullName:
                errors.append('Full name is required.')
            elif len(fullName) < 2:
                errors.append('Full name must be at least 2 characters.')
            elif re.search(r'[^a-zA-Z\s]', fullName):
                errors.append('Full name must contain letters only.')

            # Gender
            if not gender:
                errors.append('Please select a gender.')
            elif not Genders.objects.filter(pk=gender).exists():
                errors.append('Selected gender is invalid.')

            # Birth date
            if not birthDate:
                errors.append('Birth date is required.')
            else:
                try:
                    birth = datetime.strptime(birthDate, '%Y-%m-%d').date()
                    today = date.today()
                    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
                    if birth >= today:
                        errors.append('Birth date cannot be today or in the future.')
                    elif age > 120:
                        errors.append('Please enter a valid birth date.')
                    elif age < 5:
                        errors.append('Age seems too young.')
                except ValueError:
                    errors.append('Birth date format is invalid.')

            # Address
            if not address:
                errors.append('Address is required.')
            elif len(address) < 5:
                errors.append('Address must be at least 5 characters.')

            # Contact number
            if not contactNumber:
                errors.append('Contact number is required.')
            elif not re.fullmatch(r'\d+', contactNumber):
                errors.append('Contact number must contain numbers only.')
            elif not (contactNumber.startswith('09') or contactNumber.startswith('63')):
                errors.append('Contact number must start with 09 or 63.')
            elif contactNumber.startswith('09') and len(contactNumber) != 11:
                errors.append('Contact number starting with 09 must be 11 digits.')
            elif contactNumber.startswith('63') and len(contactNumber) != 12:
                errors.append('Contact number starting with 63 must be 12 digits.')

            # Email (optional)
            if email:
                if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
                    errors.append('Please enter a valid email address.')

            if errors:
                for error in errors:
                    messages.error(request, error)
                genders = Genders.objects.all()
                return render(request, 'user/UserEdit.html', {
                    'user': user,
                    'genders': genders
                })

            # ── Save ───────────────────────────────────────────────
            user.full_name = fullName
            user.gender_id = gender
            user.birth_date = birthDate
            user.address = address
            user.contact_number = contactNumber
            user.email = email

            if request.FILES.get('profile_picture'):
                if user.profile_picture:
                    import os
                    if os.path.isfile(user.profile_picture.path):
                        os.remove(user.profile_picture.path)
                user.profile_picture = request.FILES.get('profile_picture')

            user.save()
            messages.success(request, 'User updated successfully!')
            return redirect('/user/list')

        genders = Genders.objects.all()
        data = {
            'user': user,
            'genders': genders
        }
        return render(request, 'user/UserEdit.html', data)
    except Exception as e:
        return HttpResponse(f'Error occurred during user edit: {e}')
    
def user_delete_picture(request, user_id):
    try:
        user = Users.objects.get(user_id=user_id)
        if user.profile_picture:
            import os
            if os.path.isfile(user.profile_picture.path):
                os.remove(user.profile_picture.path)
            user.profile_picture = None
            user.save()
            messages.success(request, 'Profile picture removed.')
        return redirect(f'/user/edit/{user_id}')
    except Exception as e:
        return HttpResponse(f'Error occurred during delete picture: {e}')

def user_search_suggestions(request):
    try:
        query = request.GET.get('q', '').strip()

        if not query or len(query) < 1:
            return JsonResponse({'suggestions': []})

        users = Users.objects.select_related('gender').filter(
            Q(full_name__icontains=query) |
            Q(username__icontains=query) |
            Q(address__icontains=query) |
            Q(contact_number__icontains=query) |
            Q(gender__gender__icontains=query) |
            Q(birth_date__icontains=query) |
            Q(email__icontains=query)
        )[:10]

        suggestions = set()

        for user in users:
            fields = [
                user.full_name,
                user.username,
                user.address,
                user.contact_number,
                user.gender.gender if user.gender else '',
                str(user.birth_date) if user.birth_date else '',
                user.email or '',
            ]
            for field in fields:
                if field and query.lower() in field.lower():
                    suggestions.add(field)

        return JsonResponse({'suggestions': list(suggestions)[:8]})

    except Exception as e:
        return JsonResponse({'suggestions': [], 'error': str(e)})