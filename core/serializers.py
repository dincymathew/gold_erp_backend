from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['username'] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['role'] = self.user.role
        data['username'] = self.user.username
        data['branch_id'] = self.user.branch_id
        if self.user.branch:
            data['branch_name'] = self.user.branch.name
            data['x_factor'] = float(self.user.branch.x_factor)
        else:
            data['branch_name'] = 'Global HQ'
            data['x_factor'] = 92.0
        return data
