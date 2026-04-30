from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import User, UserLog
from apps.branches.models import Branch, UOM, Currency, Expense

class BranchSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    class Meta:
        model = Branch
        fields = ['id', 'name', 'location', 'x_factor', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['created_by']

class ExpenseSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False)
    class Meta:
        model = Expense
        fields = ['id', 'branch', 'branch_name', 'category', 'status', 'source_name', 'description', 'rate_per_gram', 'grams', 'total', 'date', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['status', 'created_by']

class UOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = UOM
        fields = '__all__'

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'branch', 'branch_name', 'last_login', 'is_active', 'password', 'created_by', 'created_by_name']
        read_only_fields = ['created_by']

class UserLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = UserLog
        fields = '__all__'

class UserCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = self.request.user
        branch = serializer.validated_data.get('branch')
        requested_role = serializer.validated_data.get('role')

        if user.role == 'MANAGER':
            branch = user.branch
            if requested_role in ['SUPER_ADMIN', 'ADMIN', 'MANAGER']:
                raise serializers.ValidationError("Managers can only create staff.")
        
        if user.role == 'ADMIN':
            if requested_role in ['SUPER_ADMIN', 'ADMIN']:
                raise serializers.ValidationError("Admins cannot create other admins or super admins.")
        
        if user.role != 'SUPER_ADMIN' and requested_role == 'SUPER_ADMIN':
            raise serializers.ValidationError("Only Super Admins can create other Super Admins.")
            
        # Extract password before saving
        password = serializer.validated_data.pop('password', None)
        new_user = serializer.save(branch=branch, created_by=user)
        
        if password:
            new_user.set_password(password)
            new_user.save()
        
        UserLog.objects.create(
            user=user,
            role=user.role,
            action="CREATE_USER",
            details=f"Created {new_user.role}: {new_user.username} for branch: {new_user.branch.name if new_user.branch else 'Global'}"
        )

class UserListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    def get_queryset(self):
        user = self.request.user
        if user.role in ['SUPER_ADMIN', 'ADMIN']:
            return User.objects.all().order_by('-id')
        elif user.role == 'MANAGER':
            return User.objects.filter(branch=user.branch).order_by('-id')
        return User.objects.none()

class UserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def perform_update(self, serializer):
        user = serializer.save()
        password = self.request.data.get('password')
        if password:
            user.set_password(password)
            user.save()
            
        UserLog.objects.create(
            user=self.request.user,
            role=self.request.user.role,
            action="UPDATE_USER",
            details=f"Updated user: {user.username} ({user.role})"
        )

class UserDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Log before deletion
        UserLog.objects.create(
            user=self.request.user,
            role=self.request.user.role,
            action="DELETE_USER",
            details=f"Permanently removed user: {instance.username} ({instance.role})"
        )
        
        # Physical deletion
        self.perform_destroy(instance)
        return Response({'status': 'success', 'message': 'User deleted permanently'}, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        instance.delete()

class UserStatusToggleView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def patch(self, request, *args, **kwargs):
        user_to_toggle = self.get_object()
        user_to_toggle.is_active = not user_to_toggle.is_active
        user_to_toggle.save()
        
        UserLog.objects.create(
            user=request.user,
            role=request.user.role,
            action="TOGGLE_USER_STATUS",
            details=f"{'Enabled' if user_to_toggle.is_active else 'Disabled'} user: {user_to_toggle.username}"
        )
        return Response({'status': 'success', 'is_active': user_to_toggle.is_active})

class BranchCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BranchSerializer

    def perform_create(self, serializer):
        branch = serializer.save(created_by=self.request.user)
        UserLog.objects.create(
            user=self.request.user,
            role=self.request.user.role,
            action="CREATE_BRANCH",
            details=f"Established new branch: {branch.name} with X-Factor: {branch.x_factor}"
        )

class BranchListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BranchSerializer
    queryset = Branch.objects.all().order_by('-created_at')

class BranchDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BranchSerializer
    queryset = Branch.objects.all()

    def perform_update(self, serializer):
        branch = serializer.save()
        UserLog.objects.create(
            user=self.request.user,
            role=self.request.user.role,
            action="UPDATE_BRANCH",
            details=f"Updated branch details for: {branch.name}"
        )

    def perform_destroy(self, instance):
        UserLog.objects.create(
            user=self.request.user,
            role=self.request.user.role,
            action="DELETE_BRANCH",
            details=f"Removed branch: {instance.name}"
        )
        instance.delete()

class UserLogListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserLogSerializer
    def get_queryset(self):
        # Allow Admin and Manager to view logs (can be filtered by role/branch in future if needed)
        return UserLog.objects.all().order_by('-created_at')

class UOMListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UOMSerializer
    queryset = UOM.objects.all()

class CurrencyListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()

class ExpenseCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExpenseSerializer
    def perform_create(self, serializer):
        user = self.request.user
        branch = serializer.validated_data.get('branch')
        if user.role == 'MANAGER':
            branch = user.branch
        
        # Admin creates approved expenses, Manager creates pending
        status = 'APPROVED' if user.role == 'ADMIN' else 'PENDING'
        expense = serializer.save(branch=branch, created_by=user, status=status)
        
        UserLog.objects.create(
            user=user,
            role=user.role,
            action="CREATE_EXPENSE",
            details=f"Recorded expense: {expense.grams}g @ {expense.rate_per_gram}/g for {expense.source_name}"
        )

class ExpenseListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExpenseSerializer
    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Expense.objects.all().order_by('-date')
        elif user.role == 'MANAGER':
            return Expense.objects.filter(branch=user.branch).order_by('-date')
        return Expense.objects.none()

class ExpenseStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExpenseSerializer
    queryset = Expense.objects.all()

    def patch(self, request, *args, **kwargs):
        if request.user.role != 'ADMIN':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        expense = self.get_object()
        new_status = request.data.get('status')
        if new_status not in ['APPROVED', 'REJECTED']:
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        expense.status = new_status
        expense.save()

        UserLog.objects.create(
            user=request.user,
            role=request.user.role,
            action=f"EXPENSE_{new_status}",
            details=f"Admin {request.user.username} {new_status.lower()} expense ID {expense.id} from {expense.source_name}"
        )
        return Response({'status': 'success', 'expense_status': expense.status})
