from django.contrib import admin

from .models import UserFoodgram


class CustomUserAdmin(admin.ModelAdmin):

    list_display = (
        'pk',
        'username',
    )
    search_fields = ('username',)
    list_filter = ('username',)
    empty_value_display = '-пусто-'

    def get_model_perms(self, request):
        return {
            'add': self.has_add_permission(request),
            'delete': self.has_delete_permission(request),
            'view': self.has_view_permission(request),
        }


admin.site.register(UserFoodgram, CustomUserAdmin)