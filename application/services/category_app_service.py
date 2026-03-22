from application.dto.category import CategoryCreateRequest
from infra.db.models import CategoryModel
from infra.db.repositories import CategoryRepository, HouseholdRepository


class CategoryAppService:
    def __init__(self, category_repo: CategoryRepository, household_repo: HouseholdRepository) -> None:
        self.category_repo = category_repo
        self.household_repo = household_repo

    def create_category(self, request: CategoryCreateRequest) -> CategoryModel:
        self.household_repo.get(request.household_id)
        if request.parent_id:
            self.category_repo.get_for_household(category_id=request.parent_id, household_id=request.household_id)
        return self.category_repo.create(**request.model_dump())

    def list_categories(self, household_id: str) -> list[CategoryModel]:
        self.household_repo.get(household_id)
        return self.category_repo.list_by_household(household_id)
