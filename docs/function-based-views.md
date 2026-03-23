# Function-Based Views

Pass `request` when constructing the form:

```python
def contact_view(request):
    form = ContactForm(request.POST or None, request=request)
    if request.method == 'POST' and form.is_valid():
        send_email(form.cleaned_data)
        return redirect('/thanks/')
    return render(request, 'contact.html', {'form': form})
```

Guard checks run automatically inside `is_valid()`. If any check triggers,
the form is invalid and `form.guard_failures` contains the results.

## Custom failure handling

Check `form.guard_failures` after `is_valid()` returns `False`:

```python
def contact_view(request):
    form = ContactForm(request.POST or None, request=request)
    if request.method == 'POST':
        if form.is_valid():
            send_email(form.cleaned_data)
            return redirect('/thanks/')
        if form.guard_failures:
            return redirect('/thanks/')  # silent reject
    return render(request, 'contact.html', {'form': form})
```
