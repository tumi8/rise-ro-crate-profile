# flake8: noqa
# pylint: disable=all
# pyrefly: ignore-errors

from __future__ import annotations
from typing import Optional, List, Union, Literal, Any
from pydantic import BaseModel, Field, ConfigDict


class EntityReference(BaseModel):
    """Reference to another entity by @id."""
    id: str = Field(..., alias='@id')

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class Person(BaseModel):
    """A person"""
    id: str = Field(..., alias='@id')
    type: Literal['Person'] = Field(default='Person', alias='@type')
    givenName: Optional[str] = None  # Given name
    familyName: Optional[str] = None  # Family name
    name: str  # Full name
    alternateName: Optional[str] = None  # Alternate name
    affiliation: Optional[EntityReference] = None  # Affiliated organization

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class Organization(BaseModel):
    """An organization"""
    id: str = Field(..., alias='@id')
    type: Literal['Organization'] = Field(default='Organization', alias='@type')
    name: str  # Organization name
    alternateName: Optional[str] = None  # Alternate name
    location: Optional[str] = None  # Location
    url: Optional[str] = None  # URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class Role(BaseModel):
    """A role assigned to a contributor"""
    id: str = Field(..., alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: str  # Name of the role
    description: Optional[str] = None  # Role description
    url: Optional[str] = None  # Role URL
    contributor: List[EntityReference]  # Contributors with this role

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreativeWork(BaseModel):
    """A creative work reference"""
    id: str = Field(..., alias='@id')
    type: Literal['CreativeWork'] = Field(default='CreativeWork', alias='@type')
    name: str  # Name of the creative work
    description: Optional[str] = None  # Description
    alternateName: Optional[str] = None  # Short name
    citation: Optional[str] = None  # Citation URL
    version: Optional[str] = None  # Version
    url: Optional[str] = None  # URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class ScholarlyArticle(CreativeWork):
    """A scholarly article (subtype of CreativeWork)"""
    type: Literal['ScholarlyArticle'] = Field(default='ScholarlyArticle', alias='@type')

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class WebPage(BaseModel):
    """Archived webpage reference"""
    id: str = Field(..., alias='@id')
    type: Literal['WebPage'] = Field(default='WebPage', alias='@type')
    name: str  # Page name
    dateCreated: Optional[str] = None  # Creation date
    datePublished: Optional[str] = None  # Publication date
    identifier: Optional[str] = None  # Identifier
    keywords: Optional[List[str]] = None  # Keywords
    license: Optional[Union[str, EntityReference]] = None  # License
    publisher: Optional[Union[str, EntityReference]] = None  # Publisher

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class License(BaseModel):
    """A license entity (CreativeWork)"""
    id: str = Field(..., alias='@id')
    type: Literal['CreativeWork'] = Field(default='CreativeWork', alias='@type')
    name: str  # License full name
    alternateName: str  # SPDX short identifier
    url: str  # License URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleDefinition(BaseModel):
    """A CRediT role definition (without contributor assignment)"""
    id: str = Field(..., alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: str  # Name of the role
    description: Optional[str] = None  # Role description
    url: Optional[str] = None  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class FileType(BaseModel):
    """A file type/format definition"""
    id: str = Field(..., alias='@id')
    type: List[Literal['WebPage', 'Standard']] = Field(default=['WebPage', 'Standard'], alias='@type')
    name: str  # Format name

    model_config = ConfigDict(populate_by_name=True, extra='forbid')
