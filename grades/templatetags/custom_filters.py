from django import template

register = template.Library()

# --- FILTRES DE BASE ---
@register.filter
def get_item(dictionary, key):
    """Retourne la valeur d'un dictionnaire par sa clé"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def has_key(dictionary, key):
    """Vérifie si une clé existe dans le dictionnaire"""
    if not dictionary or not isinstance(dictionary, dict):
        return False
    return key in dictionary

@register.filter
def subtract(value, arg):
    """Soustrait arg de value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        try:
            return float(value) - float(arg)
        except (ValueError, TypeError):
            return value

@register.filter
def percentage(value, total):
    """Retourne le pourcentage de value par rapport à total"""
    try:
        if total == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def split(value, arg):
    """Split une chaîne par un séparateur"""
    return value.split(arg)

# --- FILTRES POUR LES NOTES ---
@register.filter
def mention_note(valeur):
    """Retourne la mention selon la valeur de la note"""
    try:
        valeur = float(valeur)
        if valeur >= 90:
            return "Excellent"
        elif valeur >= 80:
            return "Très bien"
        elif valeur >= 70:
            return "Bien"
        elif valeur >= 60:
            return "Assez bien"
        elif valeur >= 50:
            return "Passable"
        else:
            return "Insuffisant"
    except (ValueError, TypeError):
        return "N/A"

@register.filter
def couleur_mention(valeur):
    """Retourne la couleur Bootstrap selon la note (échelle standard)"""
    try:
        valeur = float(valeur)
        if valeur >= 90:
            return "success"
        elif valeur >= 80:
            return "primary"
        elif valeur >= 70:
            return "info"
        elif valeur >= 60:
            return "warning"
        elif valeur >= 50:
            return "secondary"
        else:
            return "danger"
    except (ValueError, TypeError):
        return "secondary"

@register.filter
def couleur_mention_70(valeur):
    """Retourne la couleur Bootstrap basée sur 70/100 comme seuil"""
    try:
        valeur = float(valeur)
        if valeur >= 70:
            return "success"      # Validé (≥ 70)
        elif valeur >= 50:
            return "warning"      # Risque
        else:
            return "danger"       # Échec
    except (ValueError, TypeError):
        return "secondary"

# --- FILTRES POUR LES STATUTS ---
@register.filter
def status_color(statut):
    """Retourne la couleur Bootstrap selon le statut"""
    colors = {
        'brouillon': 'info',
        'soumise': 'warning',
        'publiée': 'success',
        'rejetée': 'danger',
    }
    return colors.get(statut, 'secondary')

# --- FILTRES DE CALCUL ---
@register.filter
def average(queryset, field_name):
    """Calcule la moyenne d'un champ dans un queryset"""
    total = 0
    count = 0
    for item in queryset:
        value = getattr(item, field_name, None)
        if value is not None:
            total += float(value)
            count += 1
    return total / count if count > 0 else 0

@register.filter
def min_value(queryset, field_name):
    """Trouve la valeur minimum"""
    values = [getattr(item, field_name) for item in queryset if hasattr(item, field_name)]
    return min(values) if values else 0

@register.filter
def max_value(queryset, field_name):
    """Trouve la valeur maximum"""
    values = [getattr(item, field_name) for item in queryset if hasattr(item, field_name)]
    return max(values) if values else 0

# --- TAGS PERSONNALISÉS ---
@register.simple_tag
def get_note_for_cours(cours_avec_notes, cours_id):
    """Retourne la note pour un cours donné - DEBUG VERSION"""
    print(f"DEBUG get_note_for_cours: cours_id={cours_id}")
    print(f"DEBUG cours_avec_notes type: {type(cours_avec_notes)}")
    
    if not cours_avec_notes:
        print(f"DEBUG: cours_avec_notes est vide")
        return None
    
    for item in cours_avec_notes:
        cours = item.get('cours')
        note = item.get('note')
        print(f"DEBUG: Item - cours_id={cours.id if cours else 'None'}, note={note}")
        
        if cours and cours.id == cours_id:
            print(f"DEBUG: Note trouvée! {note}")
            return note
    
    print(f"DEBUG: Aucune note trouvée pour cours_id={cours_id}")
    return None
