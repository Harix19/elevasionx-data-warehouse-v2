"""Tests for Contact API endpoints.

Stories 3.1-3.5: Contact Management
"""

import pytest
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.contact import Contact


# ============================================================================
# Story 3.1: Create Contact with Company Link
# ============================================================================


@pytest.mark.asyncio
async def test_create_contact_with_company(async_client: AsyncClient, db: AsyncSession):
    """Test creating a contact linked to a company populates snapshot fields."""
    # Create a company first
    company = Company(
        name="Test Corp",
        domain="testcorp.com",
        linkedin_url="https://linkedin.com/company/testcorp",
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)

    # Create contact linked to company
    response = await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@testcorp.com",
            "company_id": str(company.id),
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["full_name"] == "John Doe"
    assert data["company_id"] == str(company.id)
    # Snapshot fields populated from company
    assert data["working_company_name"] == "Test Corp"
    assert data["company_domain"] == "testcorp.com"
    assert data["company_linkedin_url"] == "https://linkedin.com/company/testcorp"


@pytest.mark.asyncio
async def test_create_contact_without_company(async_client: AsyncClient, db: AsyncSession):
    """Test creating a contact without company link."""
    response = await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Smith"
    assert data["full_name"] == "Jane Smith"
    assert data["company_id"] is None
    assert data["working_company_name"] is None


@pytest.mark.asyncio
async def test_create_contact_full_name_auto_generation(async_client: AsyncClient, db: AsyncSession):
    """Test that full_name is auto-generated from first_name + last_name."""
    response = await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Alice",
            "last_name": "Wonderland",
        },
    )

    assert response.status_code == 201
    assert response.json()["full_name"] == "Alice Wonderland"


@pytest.mark.asyncio
async def test_create_contact_missing_required_fields(async_client: AsyncClient, db: AsyncSession):
    """Test validation error for missing first_name/last_name."""
    response = await async_client.post(
        "/api/v1/contacts/",
        json={
            "email": "test@example.com",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_contact_invalid_company_id(async_client: AsyncClient, db: AsyncSession):
    """Test 404 when company_id references non-existent company."""
    response = await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Bob",
            "last_name": "Builder",
            "company_id": str(uuid4()),
        },
    )

    assert response.status_code == 404
    assert "Company not found" in response.json()["detail"]


# ============================================================================
# Story 3.2: Read and Update Contact
# ============================================================================


@pytest.mark.asyncio
async def test_get_contact(async_client: AsyncClient, db: AsyncSession):
    """Test getting an existing contact."""
    contact = Contact(
        first_name="Get",
        last_name="Test",
        full_name="Get Test",
        email="get@test.com",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    response = await async_client.get(f"/api/v1/contacts/{contact.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Get"
    assert data["last_name"] == "Test"
    assert data["email"] == "get@test.com"


@pytest.mark.asyncio
async def test_get_contact_not_found(async_client: AsyncClient, db: AsyncSession):
    """Test 404 for non-existent contact."""
    response = await async_client.get(f"/api/v1/contacts/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_deleted_contact_returns_404(async_client: AsyncClient, db: AsyncSession):
    """Test that GET returns 404 for soft-deleted contact."""
    from datetime import datetime, timezone

    contact = Contact(
        first_name="Deleted",
        last_name="Contact",
        full_name="Deleted Contact",
        deleted_at=datetime.now(timezone.utc),
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    response = await async_client.get(f"/api/v1/contacts/{contact.id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_contact_partial_update(async_client: AsyncClient, db: AsyncSession):
    """Test partial update of contact."""
    contact = Contact(
        first_name="Patch",
        last_name="Test",
        full_name="Patch Test",
        email="patch@test.com",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    response = await async_client.patch(
        f"/api/v1/contacts/{contact.id}",
        json={"email": "updated@test.com"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@test.com"
    assert data["first_name"] == "Patch"  # Unchanged


@pytest.mark.asyncio
async def test_patch_contact_regenerates_full_name(async_client: AsyncClient, db: AsyncSession):
    """Test that full_name regenerates when first_name or last_name changes."""
    contact = Contact(
        first_name="Old",
        last_name="Name",
        full_name="Old Name",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    response = await async_client.patch(
        f"/api/v1/contacts/{contact.id}",
        json={"first_name": "New"},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"


@pytest.mark.asyncio
async def test_patch_contact_updated_at_changes(async_client: AsyncClient, db: AsyncSession):
    """Test that updated_at changes after PATCH."""
    contact = Contact(
        first_name="Update",
        last_name="Time",
        full_name="Update Time",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    original_updated_at = contact.updated_at

    # Small delay to ensure time difference
    import asyncio
    await asyncio.sleep(0.1)

    response = await async_client.patch(
        f"/api/v1/contacts/{contact.id}",
        json={"email": "time@test.com"},
    )

    assert response.status_code == 200
    new_updated_at = response.json()["updated_at"]
    assert new_updated_at != original_updated_at.isoformat()


# ============================================================================
# Story 3.3: Soft Delete and Restore Contact
# ============================================================================


@pytest.mark.asyncio
async def test_delete_contact_sets_deleted_at(async_client: AsyncClient, db: AsyncSession):
    """Test DELETE sets deleted_at and returns 204."""
    contact = Contact(
        first_name="Delete",
        last_name="Me",
        full_name="Delete Me",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    response = await async_client.delete(f"/api/v1/contacts/{contact.id}")

    assert response.status_code == 204

    # Verify deleted_at is set
    await db.refresh(contact)
    assert contact.deleted_at is not None


@pytest.mark.asyncio
async def test_get_after_delete_returns_404(async_client: AsyncClient, db: AsyncSession):
    """Test GET returns 404 after DELETE."""
    contact = Contact(
        first_name="Gone",
        last_name="Contact",
        full_name="Gone Contact",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    await async_client.delete(f"/api/v1/contacts/{contact.id}")
    response = await async_client.get(f"/api/v1/contacts/{contact.id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_non_existent_returns_404(async_client: AsyncClient, db: AsyncSession):
    """Test DELETE returns 404 for non-existent contact."""
    response = await async_client.delete(f"/api/v1/contacts/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_restore_contact_clears_deleted_at(async_client: AsyncClient, db: AsyncSession):
    """Test restore clears deleted_at and returns 200."""
    from datetime import datetime, timezone

    contact = Contact(
        first_name="Restore",
        last_name="Me",
        full_name="Restore Me",
        deleted_at=datetime.now(timezone.utc),
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    response = await async_client.post(f"/api/v1/contacts/{contact.id}/restore")

    assert response.status_code == 200
    data = response.json()
    assert data["deleted_at"] is None
    assert data["first_name"] == "Restore"


@pytest.mark.asyncio
async def test_get_after_restore_works(async_client: AsyncClient, db: AsyncSession):
    """Test GET works after restore."""
    from datetime import datetime, timezone

    contact = Contact(
        first_name="Restored",
        last_name="Contact",
        full_name="Restored Contact",
        deleted_at=datetime.now(timezone.utc),
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    await async_client.post(f"/api/v1/contacts/{contact.id}/restore")
    response = await async_client.get(f"/api/v1/contacts/{contact.id}")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_restore_non_deleted_returns_400(async_client: AsyncClient, db: AsyncSession):
    """Test restore returns 400 if contact is not deleted."""
    contact = Contact(
        first_name="Not",
        last_name="Deleted",
        full_name="Not Deleted",
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    response = await async_client.post(f"/api/v1/contacts/{contact.id}/restore")

    assert response.status_code == 400
    assert "not deleted" in response.json()["detail"]


@pytest.mark.asyncio
async def test_restore_non_existent_returns_404(async_client: AsyncClient, db: AsyncSession):
    """Test restore returns 404 for non-existent contact."""
    response = await async_client.post(f"/api/v1/contacts/{uuid4()}/restore")

    assert response.status_code == 404


# ============================================================================
# Story 3.4: View Contacts for a Company
# ============================================================================


@pytest.mark.asyncio
async def test_list_contacts_for_company(async_client: AsyncClient, db: AsyncSession):
    """Test listing contacts for a company."""
    company = Company(name="Contacts Corp", domain="contacts.com")
    db.add(company)
    await db.commit()
    await db.refresh(company)

    # Create two contacts for this company
    contact1 = Contact(
        first_name="First",
        last_name="Contact",
        full_name="First Contact",
        company_id=company.id,
    )
    contact2 = Contact(
        first_name="Second",
        last_name="Contact",
        full_name="Second Contact",
        company_id=company.id,
    )
    db.add_all([contact1, contact2])
    await db.commit()

    response = await async_client.get(f"/api/v1/companies/{company.id}/contacts")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_list_contacts_empty_for_company_without_contacts(async_client: AsyncClient, db: AsyncSession):
    """Test empty list for company without contacts."""
    company = Company(name="Empty Corp", domain="empty.com")
    db.add(company)
    await db.commit()
    await db.refresh(company)

    response = await async_client.get(f"/api/v1/companies/{company.id}/contacts")

    assert response.status_code == 200
    assert response.json()["items"] == []


@pytest.mark.asyncio
async def test_list_contacts_404_for_non_existent_company(async_client: AsyncClient, db: AsyncSession):
    """Test 404 for non-existent company."""
    response = await async_client.get(f"/api/v1/companies/{uuid4()}/contacts")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_contacts_404_for_deleted_company(async_client: AsyncClient, db: AsyncSession):
    """Test 404 for deleted company."""
    from datetime import datetime, timezone

    company = Company(
        name="Deleted Corp",
        domain="deleted.com",
        deleted_at=datetime.now(timezone.utc),
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)

    response = await async_client.get(f"/api/v1/companies/{company.id}/contacts")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_contacts_include_deleted_parameter(async_client: AsyncClient, db: AsyncSession):
    """Test include_deleted parameter."""
    from datetime import datetime, timezone

    company = Company(name="Mixed Corp", domain="mixed.com")
    db.add(company)
    await db.commit()
    await db.refresh(company)

    contact1 = Contact(
        first_name="Active",
        last_name="Contact",
        full_name="Active Contact",
        company_id=company.id,
    )
    contact2 = Contact(
        first_name="Deleted",
        last_name="Contact",
        full_name="Deleted Contact",
        company_id=company.id,
        deleted_at=datetime.now(timezone.utc),
    )
    db.add_all([contact1, contact2])
    await db.commit()

    # Without include_deleted - should only get active contact
    response = await async_client.get(f"/api/v1/companies/{company.id}/contacts")
    assert len(response.json()["items"]) == 1

    # With include_deleted=true - should get both
    response = await async_client.get(f"/api/v1/companies/{company.id}/contacts?include_deleted=true")
    assert len(response.json()["items"]) == 2


@pytest.mark.asyncio
async def test_list_contacts_ordered_by_created_at_desc(async_client: AsyncClient, db: AsyncSession):
    """Test contacts are ordered by created_at DESC."""
    import asyncio

    company = Company(name="Ordered Corp", domain="ordered.com")
    db.add(company)
    await db.commit()
    await db.refresh(company)

    # Create contacts with slight delays to ensure different timestamps
    contact1 = Contact(
        first_name="First",
        last_name="Created",
        full_name="First Created",
        company_id=company.id,
    )
    db.add(contact1)
    await db.commit()

    await asyncio.sleep(0.1)

    contact2 = Contact(
        first_name="Second",
        last_name="Created",
        full_name="Second Created",
        company_id=company.id,
    )
    db.add(contact2)
    await db.commit()

    response = await async_client.get(f"/api/v1/companies/{company.id}/contacts")

    items = response.json()["items"]
    assert items[0]["first_name"] == "Second"  # Most recent first
    assert items[1]["first_name"] == "First"


# ============================================================================
# Story 3.5: Contact Tagging
# ============================================================================


@pytest.mark.asyncio
async def test_create_contact_with_all_tag_categories(async_client: AsyncClient, db: AsyncSession):
    """Test creating contact with all three tag categories."""
    response = await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Tagged",
            "last_name": "Contact",
            "custom_tags_a": ["vip", "priority"],
            "custom_tags_b": ["tech", "startup"],
            "custom_tags_c": ["inbound"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["custom_tags_a"] == ["vip", "priority"]
    assert data["custom_tags_b"] == ["tech", "startup"]
    assert data["custom_tags_c"] == ["inbound"]


@pytest.mark.asyncio
async def test_partial_update_one_tag_array(async_client: AsyncClient, db: AsyncSession):
    """Test partial update of one tag array leaves others unchanged."""
    contact = Contact(
        first_name="Tag",
        last_name="Test",
        full_name="Tag Test",
        custom_tags_a=["original_a"],
        custom_tags_b=["original_b"],
        custom_tags_c=["original_c"],
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    response = await async_client.patch(
        f"/api/v1/contacts/{contact.id}",
        json={"custom_tags_a": ["updated_a"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["custom_tags_a"] == ["updated_a"]
    assert data["custom_tags_b"] == ["original_b"]  # Unchanged
    assert data["custom_tags_c"] == ["original_c"]  # Unchanged


@pytest.mark.asyncio
async def test_clear_tags_with_empty_array(async_client: AsyncClient, db: AsyncSession):
    """Test clearing tags with empty array."""
    contact = Contact(
        first_name="Clear",
        last_name="Tags",
        full_name="Clear Tags",
        custom_tags_a=["to_clear"],
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    response = await async_client.patch(
        f"/api/v1/contacts/{contact.id}",
        json={"custom_tags_a": []},
    )

    assert response.status_code == 200
    assert response.json()["custom_tags_a"] == []


@pytest.mark.asyncio
async def test_tags_appear_in_get_response(async_client: AsyncClient, db: AsyncSession):
    """Test tags appear in GET response."""
    contact = Contact(
        first_name="Get",
        last_name="Tags",
        full_name="Get Tags",
        custom_tags_a=["tag1", "tag2"],
    )
    db.add(contact)
    await db.commit()
    await db.refresh(contact)

    response = await async_client.get(f"/api/v1/contacts/{contact.id}")

    assert response.status_code == 200
    assert response.json()["custom_tags_a"] == ["tag1", "tag2"]


@pytest.mark.asyncio
async def test_tags_case_sensitive_storage(async_client: AsyncClient, db: AsyncSession):
    """Test tags are stored with case sensitivity."""
    response = await async_client.post(
        "/api/v1/contacts/",
        json={
            "first_name": "Case",
            "last_name": "Test",
            "custom_tags_a": ["VIP", "vip", "Vip"],
        },
    )

    assert response.status_code == 201
    # All three should be stored as-is (case-sensitive)
    assert response.json()["custom_tags_a"] == ["VIP", "vip", "Vip"]
