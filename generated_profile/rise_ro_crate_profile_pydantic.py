"""
Auto-generated Pydantic models for Research Infrastructure Shareable Experiments RO-Crate Profile (RISE RO-Crate Profile)
Version: 1.0.0
"""

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


class LicenseApache20(License):
    """Apache License 2.0"""
    id: Literal['https://www.apache.org/licenses/LICENSE-2.0'] = Field(default='https://www.apache.org/licenses/LICENSE-2.0', alias='@id')
    type: Literal['CreativeWork'] = Field(default='CreativeWork', alias='@type')
    name: Literal['Apache License 2.0'] = Field(default='Apache License 2.0')  # License full name
    alternateName: Literal['Apache-2.0'] = Field(default='Apache-2.0')  # SPDX short identifier
    url: Literal['https://www.apache.org/licenses/LICENSE-2.0'] = Field(default='https://www.apache.org/licenses/LICENSE-2.0')  # License URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class LicenseCcBy40(License):
    """Creative Commons Attribution 4.0 International"""
    id: Literal['https://creativecommons.org/licenses/by/4.0/legalcode'] = Field(default='https://creativecommons.org/licenses/by/4.0/legalcode', alias='@id')
    type: Literal['CreativeWork'] = Field(default='CreativeWork', alias='@type')
    name: Literal['Creative Commons Attribution 4.0 International'] = Field(default='Creative Commons Attribution 4.0 International')  # License full name
    alternateName: Literal['CC-BY-4.0'] = Field(default='CC-BY-4.0')  # SPDX short identifier
    url: Literal['https://creativecommons.org/licenses/by/4.0/legalcode'] = Field(default='https://creativecommons.org/licenses/by/4.0/legalcode')  # License URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class LicenseCcBySa40(License):
    """Creative Commons Attribution Share Alike 4.0 International"""
    id: Literal['https://creativecommons.org/licenses/by-sa/4.0/legalcode'] = Field(default='https://creativecommons.org/licenses/by-sa/4.0/legalcode', alias='@id')
    type: Literal['CreativeWork'] = Field(default='CreativeWork', alias='@type')
    name: Literal['Creative Commons Attribution Share Alike 4.0 International'] = Field(default='Creative Commons Attribution Share Alike 4.0 International')  # License full name
    alternateName: Literal['CC-BY-SA-4.0'] = Field(default='CC-BY-SA-4.0')  # SPDX short identifier
    url: Literal['https://creativecommons.org/licenses/by-sa/4.0/legalcode'] = Field(default='https://creativecommons.org/licenses/by-sa/4.0/legalcode')  # License URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class LicenseCc010(License):
    """Creative Commons Zero v1.0 Universal"""
    id: Literal['https://creativecommons.org/publicdomain/zero/1.0/legalcode'] = Field(default='https://creativecommons.org/publicdomain/zero/1.0/legalcode', alias='@id')
    type: Literal['CreativeWork'] = Field(default='CreativeWork', alias='@type')
    name: Literal['Creative Commons Zero v1.0 Universal'] = Field(default='Creative Commons Zero v1.0 Universal')  # License full name
    alternateName: Literal['CC0-1.0'] = Field(default='CC0-1.0')  # SPDX short identifier
    url: Literal['https://creativecommons.org/publicdomain/zero/1.0/legalcode'] = Field(default='https://creativecommons.org/publicdomain/zero/1.0/legalcode')  # License URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class LicenseGpl30OrLater(License):
    """GNU General Public License v3.0 or later"""
    id: Literal['https://www.gnu.org/licenses/gpl-3.0.html'] = Field(default='https://www.gnu.org/licenses/gpl-3.0.html', alias='@id')
    type: Literal['CreativeWork'] = Field(default='CreativeWork', alias='@type')
    name: Literal['GNU General Public License v3.0 or later'] = Field(default='GNU General Public License v3.0 or later')  # License full name
    alternateName: Literal['GPL-3.0-or-later'] = Field(default='GPL-3.0-or-later')  # SPDX short identifier
    url: Literal['https://www.gnu.org/licenses/gpl-3.0.html'] = Field(default='https://www.gnu.org/licenses/gpl-3.0.html')  # License URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class LicenseMit(License):
    """MIT License"""
    id: Literal['https://opensource.org/licenses/MIT'] = Field(default='https://opensource.org/licenses/MIT', alias='@id')
    type: Literal['CreativeWork'] = Field(default='CreativeWork', alias='@type')
    name: Literal['MIT License'] = Field(default='MIT License')  # License full name
    alternateName: Literal['MIT'] = Field(default='MIT')  # SPDX short identifier
    url: Literal['https://opensource.org/licenses/MIT'] = Field(default='https://opensource.org/licenses/MIT')  # License URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


AvailableLicenses = Union[LicenseApache20, LicenseCcBy40, LicenseCcBySa40, LicenseCc010, LicenseGpl30OrLater, LicenseMit]
"""Union of all available license types defined in this profile."""


class CreditRoleConceptualization(CreditRoleDefinition):
    """Conceptualization: Ideas; formulation or evolution of overarching research goals and aims."""
    id: Literal['https://credit.niso.org/contributor-roles/conceptualization/'] = Field(default='https://credit.niso.org/contributor-roles/conceptualization/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Conceptualization'] = Field(default='Conceptualization')  # Role name
    description: Literal['Ideas; formulation or evolution of overarching research goals and aims.'] = Field(default='Ideas; formulation or evolution of overarching research goals and aims.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/conceptualization/'] = Field(default='https://credit.niso.org/contributor-roles/conceptualization/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleDataCuration(CreditRoleDefinition):
    """Data curation: Management activities to annotate (produce metadata), scrub data and maintain research data (including software code, where it is necessary for interpreting the data itself) for initial use and later reuse."""
    id: Literal['https://credit.niso.org/contributor-roles/data-curation/'] = Field(default='https://credit.niso.org/contributor-roles/data-curation/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Data curation'] = Field(default='Data curation')  # Role name
    description: Literal['Management activities to annotate (produce metadata), scrub data and maintain research data (including software code, where it is necessary for interpreting the data itself) for initial use and later reuse.'] = Field(default='Management activities to annotate (produce metadata), scrub data and maintain research data (including software code, where it is necessary for interpreting the data itself) for initial use and later reuse.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/data-curation/'] = Field(default='https://credit.niso.org/contributor-roles/data-curation/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleFormalAnalysis(CreditRoleDefinition):
    """Formal analysis: Application of statistical, mathematical, computational, or other formal techniques to analyse or synthesize study data."""
    id: Literal['https://credit.niso.org/contributor-roles/formal-analysis/'] = Field(default='https://credit.niso.org/contributor-roles/formal-analysis/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Formal analysis'] = Field(default='Formal analysis')  # Role name
    description: Literal['Application of statistical, mathematical, computational, or other formal techniques to analyse or synthesize study data.'] = Field(default='Application of statistical, mathematical, computational, or other formal techniques to analyse or synthesize study data.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/formal-analysis/'] = Field(default='https://credit.niso.org/contributor-roles/formal-analysis/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleFundingAcquisition(CreditRoleDefinition):
    """Funding acquisition: Acquisition of the financial support for the project leading to this publication."""
    id: Literal['https://credit.niso.org/contributor-roles/funding-acquisition/'] = Field(default='https://credit.niso.org/contributor-roles/funding-acquisition/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Funding acquisition'] = Field(default='Funding acquisition')  # Role name
    description: Literal['Acquisition of the financial support for the project leading to this publication.'] = Field(default='Acquisition of the financial support for the project leading to this publication.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/funding-acquisition/'] = Field(default='https://credit.niso.org/contributor-roles/funding-acquisition/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleInvestigation(CreditRoleDefinition):
    """Investigation: Conducting a research and investigation process, specifically performing the experiments, or data/evidence collection."""
    id: Literal['https://credit.niso.org/contributor-roles/investigation/'] = Field(default='https://credit.niso.org/contributor-roles/investigation/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Investigation'] = Field(default='Investigation')  # Role name
    description: Literal['Conducting a research and investigation process, specifically performing the experiments, or data/evidence collection.'] = Field(default='Conducting a research and investigation process, specifically performing the experiments, or data/evidence collection.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/investigation/'] = Field(default='https://credit.niso.org/contributor-roles/investigation/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleMethodology(CreditRoleDefinition):
    """Methodology: Development or design of methodology; creation of models."""
    id: Literal['https://credit.niso.org/contributor-roles/methodology/'] = Field(default='https://credit.niso.org/contributor-roles/methodology/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Methodology'] = Field(default='Methodology')  # Role name
    description: Literal['Development or design of methodology; creation of models.'] = Field(default='Development or design of methodology; creation of models.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/methodology/'] = Field(default='https://credit.niso.org/contributor-roles/methodology/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleProjectAdministration(CreditRoleDefinition):
    """Project administration: Management and coordination responsibility for the research activity planning and execution."""
    id: Literal['https://credit.niso.org/contributor-roles/project-administration/'] = Field(default='https://credit.niso.org/contributor-roles/project-administration/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Project administration'] = Field(default='Project administration')  # Role name
    description: Literal['Management and coordination responsibility for the research activity planning and execution.'] = Field(default='Management and coordination responsibility for the research activity planning and execution.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/project-administration/'] = Field(default='https://credit.niso.org/contributor-roles/project-administration/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleResources(CreditRoleDefinition):
    """Resources: Provision of study materials, reagents, materials, patients, laboratory samples, animals, instrumentation, computing resources, or other analysis tools."""
    id: Literal['https://credit.niso.org/contributor-roles/resources/'] = Field(default='https://credit.niso.org/contributor-roles/resources/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Resources'] = Field(default='Resources')  # Role name
    description: Literal['Provision of study materials, reagents, materials, patients, laboratory samples, animals, instrumentation, computing resources, or other analysis tools.'] = Field(default='Provision of study materials, reagents, materials, patients, laboratory samples, animals, instrumentation, computing resources, or other analysis tools.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/resources/'] = Field(default='https://credit.niso.org/contributor-roles/resources/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleSoftware(CreditRoleDefinition):
    """Software: Programming, software development; designing computer programs; implementation of the computer code and supporting algorithms; testing of existing code components."""
    id: Literal['https://credit.niso.org/contributor-roles/software/'] = Field(default='https://credit.niso.org/contributor-roles/software/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Software'] = Field(default='Software')  # Role name
    description: Literal['Programming, software development; designing computer programs; implementation of the computer code and supporting algorithms; testing of existing code components.'] = Field(default='Programming, software development; designing computer programs; implementation of the computer code and supporting algorithms; testing of existing code components.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/software/'] = Field(default='https://credit.niso.org/contributor-roles/software/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleSupervision(CreditRoleDefinition):
    """Supervision: Oversight and leadership responsibility for the research activity planning and execution, including mentorship external to the core team."""
    id: Literal['https://credit.niso.org/contributor-roles/supervision/'] = Field(default='https://credit.niso.org/contributor-roles/supervision/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Supervision'] = Field(default='Supervision')  # Role name
    description: Literal['Oversight and leadership responsibility for the research activity planning and execution, including mentorship external to the core team.'] = Field(default='Oversight and leadership responsibility for the research activity planning and execution, including mentorship external to the core team.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/supervision/'] = Field(default='https://credit.niso.org/contributor-roles/supervision/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleValidation(CreditRoleDefinition):
    """Validation: Verification, whether as a part of the activity or separate, of the overall replication/reproducibility of results/experiments and other research outputs."""
    id: Literal['https://credit.niso.org/contributor-roles/validation/'] = Field(default='https://credit.niso.org/contributor-roles/validation/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Validation'] = Field(default='Validation')  # Role name
    description: Literal['Verification, whether as a part of the activity or separate, of the overall replication/reproducibility of results/experiments and other research outputs.'] = Field(default='Verification, whether as a part of the activity or separate, of the overall replication/reproducibility of results/experiments and other research outputs.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/validation/'] = Field(default='https://credit.niso.org/contributor-roles/validation/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleVisualization(CreditRoleDefinition):
    """Visualization: Preparation, creation and/or presentation of the published work, specifically visualization/data presentation."""
    id: Literal['https://credit.niso.org/contributor-roles/visualization/'] = Field(default='https://credit.niso.org/contributor-roles/visualization/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Visualization'] = Field(default='Visualization')  # Role name
    description: Literal['Preparation, creation and/or presentation of the published work, specifically visualization/data presentation.'] = Field(default='Preparation, creation and/or presentation of the published work, specifically visualization/data presentation.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/visualization/'] = Field(default='https://credit.niso.org/contributor-roles/visualization/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleWritingOriginalDraft(CreditRoleDefinition):
    """Writing - original draft: Preparation, creation and/or presentation of the published work, specifically writing the initial draft (including substantive translation)."""
    id: Literal['https://credit.niso.org/contributor-roles/writing-original-draft/'] = Field(default='https://credit.niso.org/contributor-roles/writing-original-draft/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Writing - original draft'] = Field(default='Writing - original draft')  # Role name
    description: Literal['Preparation, creation and/or presentation of the published work, specifically writing the initial draft (including substantive translation).'] = Field(default='Preparation, creation and/or presentation of the published work, specifically writing the initial draft (including substantive translation).')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/writing-original-draft/'] = Field(default='https://credit.niso.org/contributor-roles/writing-original-draft/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CreditRoleWritingReviewAndEditing(CreditRoleDefinition):
    """Writing - review & editing: Preparation, creation and/or presentation of the published work by those from the original research group, specifically critical review, commentary or revision - including pre- or post-publication stages."""
    id: Literal['https://credit.niso.org/contributor-roles/writing-review-editing/'] = Field(default='https://credit.niso.org/contributor-roles/writing-review-editing/', alias='@id')
    type: Literal['Role'] = Field(default='Role', alias='@type')
    roleName: Literal['Writing - review & editing'] = Field(default='Writing - review & editing')  # Role name
    description: Literal['Preparation, creation and/or presentation of the published work by those from the original research group, specifically critical review, commentary or revision - including pre- or post-publication stages.'] = Field(default='Preparation, creation and/or presentation of the published work by those from the original research group, specifically critical review, commentary or revision - including pre- or post-publication stages.')  # Role description
    url: Literal['https://credit.niso.org/contributor-roles/writing-review-editing/'] = Field(default='https://credit.niso.org/contributor-roles/writing-review-editing/')  # Role URL

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


AvailableCreditRoles = Union[CreditRoleConceptualization, CreditRoleDataCuration, CreditRoleFormalAnalysis, CreditRoleFundingAcquisition, CreditRoleInvestigation, CreditRoleMethodology, CreditRoleProjectAdministration, CreditRoleResources, CreditRoleSoftware, CreditRoleSupervision, CreditRoleValidation, CreditRoleVisualization, CreditRoleWritingOriginalDraft, CreditRoleWritingReviewAndEditing]
"""Union of all CRediT contributor role types defined in this profile."""


class CustomJSONDataFormat(FileType):
    """JSON Data Format"""
    id: Literal['https://www.nationalarchives.gov.uk/PRONOM/fmt/817'] = Field(default='https://www.nationalarchives.gov.uk/PRONOM/fmt/817', alias='@id')
    type: List[Literal['WebPage', 'Standard']] = Field(default=['WebPage', 'Standard'], alias='@type')
    name: Literal['JSON Data Format'] = Field(default='JSON Data Format')

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CustomPDF15Format(FileType):
    """Acrobat PDF 1.5"""
    id: Literal['https://www.nationalarchives.gov.uk/PRONOM/fmt/19'] = Field(default='https://www.nationalarchives.gov.uk/PRONOM/fmt/19', alias='@id')
    type: List[Literal['WebPage', 'Standard']] = Field(default=['WebPage', 'Standard'], alias='@type')
    name: Literal['Acrobat PDF 1.5'] = Field(default='Acrobat PDF 1.5')

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


AvailableFileTypes = Union[CustomJSONDataFormat, CustomPDF15Format]
"""Union of all AvailableFileTypes types defined in this profile."""


class Dataset(BaseModel):
    """An RO-Crate data entity for directories, listed here for reference."""

    id: str = Field(..., alias='@id')
    type: Literal['Dataset'] = Field(default='Dataset', alias='@type')
    name: str  # Directory name or human-readable name
    description: Optional[str] = None  # Description of the directory
    keywords: Optional[List[str]] = None  # Keywords of the directory
    contentSize: Optional[str] = None  # Directory size in bytes
    dateCreated: str  # Creation timestamp
    dateModified: str  # Modification timestamp
    hasPart: Optional[List[Union["Dataset", "File", EntityReference]]] = None  # Links to files in the directory
    exampleOfWork: Optional[Union["CommandFile", "LoopRun", EntityReference]] = None  # If the directory is part of a CommandFile or LoopRun

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class RootDataEntry(Dataset):
    """The root data entity that represents the crate, as defined by RO-Crate."""

    id: str = Field(..., alias='@id')
    type: Literal['RootDataEntry'] = Field(default='RootDataEntry', alias='@type')
    conformsTo: EntityReference  # Profile this crate conforms to
    name: str  # Name of the crate
    description: Optional[str] = None  # Description of the crate
    dateCreated: str  # Creation timestamp
    dateModified: str  # Modification timestamp
    datePublished: str  # Publication timestamp
    author: List[EntityReference]  # Authors of the crate
    contributor: Optional[List[EntityReference]] = None  # Authors of the crate with assigned roles
    keywords: Optional[List[str]] = None  # Keywords of the crate
    license: Optional[Union[EntityReference, str]] = None  # License of the crate
    archivedAt: Optional[List[Union[EntityReference, str]]] = None  # If copies of the crate are available online
    citation: Optional[List[EntityReference]] = None  # If the crate is used in publications
    mainEntity: Optional[Union["Experiment", EntityReference]] = None  # If the crate contains a single experiment (mutually exclusive with mentions)
    mentions: Optional[List[Union["Experiment", EntityReference]]] = None  # If the crate contains multiple experiments (mutually exclusive with mainEntity)

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class Experiment(BaseModel):
    """An experiment conducted in a research infrastructure."""

    id: str = Field(..., alias='@id')
    type: Literal['Experiment'] = Field(default='Experiment', alias='@type')
    name: Optional[str] = None  # Name of the experiment (required if the crate contains multiple experiments)
    description: Optional[str] = None  # Description of the experiment
    dateCreated: Optional[str] = None  # Creation timestamp (required if the crate contains multiple experiments)
    dateModified: Optional[str] = None  # Modification timestamp (required if the crate contains multiple experiments)
    author: Optional[List[EntityReference]] = None  # Authors of the experiment (required if the crate contains multiple experiments)
    contributor: Optional[List[EntityReference]] = None  # Authors of the experiment with assigned roles
    keywords: Optional[List[str]] = None  # Keywords of the experiment
    encodingFormat: Optional[Union[EntityReference, str]] = None  # If the identifier is a URI to a file
    executedCommands: List[Union["CommandFile", "CommandFileBootstrap", "CommandFileCopy", "CommandFileLooped", "CommandFileReset", "CommandFileSetup", EntityReference]]  # Executed commands on the experiment nodes
    resultData: Optional[List[Union["Dataset", "File", EntityReference]]] = None  # Links to result data of the executed commands
    experimentNodes: List[Union["ExperimentNode", EntityReference]]  # Experiment nodes that are part of the experiment
    experimentWorkflow: Optional[Union["File", EntityReference]] = None  # Link to a file that describes the experiment workflow
    supplementaryData: Optional[List[Union["Dataset", "File", EntityReference]]] = None  # Links to additional data that is relevant to the experiment
    includedOSImages: Optional[List[Union["OSImage", EntityReference]]] = None  # OS images that are part of the experiment
    energyMeasurements: Optional[List[Union["Dataset", "File", EntityReference]]] = None  # Links to energy measurement data of the executed commands
    experimentController: List[EntityReference]  # Software or tools used for the experiment management and execution

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class File(BaseModel):
    """An RO-Crate data entity for files. Defined as an alias for the Schema.org MediaObject type, listed here for reference."""

    id: str = Field(..., alias='@id')
    type: Literal['File'] = Field(default='File', alias='@type')
    name: str  # Filename or human-readable name
    description: Optional[str] = None  # Description of the file
    keywords: Optional[List[str]] = None  # Keywords of the file
    contentSize: str  # File size in bytes
    dateCreated: str  # Creation timestamp
    dateModified: str  # Modification timestamp
    encodingFormat: Optional[Union[EntityReference, str]] = None  # IANA mediatype or link to contextual entry
    exampleOfWork: Optional[Union["CommandFile", "LoopRun", EntityReference]] = None  # If the file is part of a CommandFile or LoopRun

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CommandFile(File):
    """A file containing commands to be executed on an experiment node."""

    id: str = Field(..., alias='@id')
    type: Literal['CommandFile'] = Field(default='CommandFile', alias='@type')
    startTime: str  # Timestamp when the command starts
    endTime: str  # Timestamp when the command finishes
    duration: str  # Duration of the command
    executedOn: Union["ExperimentNode", EntityReference]  # Experiment node executing the command
    variableSet: Optional[Union["File", EntityReference]] = None  # Link to a variable set file
    status: Union["File", str, EntityReference]  # Return code or link to the status file
    stdout: Union["File", EntityReference]  # Link to the stdout file
    stderr: Union["File", EntityReference]  # Link to the stderr file
    resultData: Optional[List[Union["Dataset", "File", EntityReference]]] = None  # Links to result data
    invokedCommands: Optional[List[Union["CommandFile", EntityReference]]] = None  # Links to invoked subcommands
    invokedBy: Optional[Union["CommandFile", "LoopRun", EntityReference]] = None  # If the command is invoked by a parent command
    energyMeasurements: Optional[List[Union["Dataset", "File", EntityReference]]] = None  # Links to energy measurement data

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CommandFileLooped(File):
    """A command file that iterates over an array of parameters."""

    id: str = Field(..., alias='@id')
    type: Literal['CommandFileLooped'] = Field(default='CommandFileLooped', alias='@type')
    startTime: str  # Timestamp when the command starts
    endTime: str  # Timestamp when the command finishes
    duration: str  # Duration of the command
    executedOn: Union["ExperimentNode", EntityReference]  # Experiment node executing the command
    variableSet: Optional[Union["File", EntityReference]] = None  # Link to a variable set file
    loopRuns: List[Union["LoopRun", EntityReference]]  # Links to the individual loop runs

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class LoopRun(File):
    """A single run of a looped command file."""

    id: str = Field(..., alias='@id')
    type: Literal['LoopRun'] = Field(default='LoopRun', alias='@type')
    startTime: str  # Timestamp when the run starts
    endTime: str  # Timestamp when the run finishes
    duration: str  # Duration of the run
    runOfLoopedCommand: Union["CommandFileLooped", EntityReference]  # Link to the looped command file
    status: Union["File", str, EntityReference]  # Return code or link to the status file
    stdout: Union["File", EntityReference]  # Link to the stdout file
    stderr: Union["File", EntityReference]  # Link to the stderr file
    resultData: Optional[List[Union["Dataset", "File", EntityReference]]] = None  # Links to result data
    invokedCommands: Optional[List[Union["CommandFile", EntityReference]]] = None  # Links to invoked subcommands
    energyMeasurements: Optional[List[Union["Dataset", "File", EntityReference]]] = None  # Links to energy measurement data

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CommandFileBootstrap(CommandFile):
    """A command file for bootstrapping an experiment node."""

    id: str = Field(..., alias='@id')
    type: Literal['CommandFileBootstrap'] = Field(default='CommandFileBootstrap', alias='@type')

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CommandFileSetup(CommandFile):
    """A command file for setting up an experiment node."""

    id: str = Field(..., alias='@id')
    type: Literal['CommandFileSetup'] = Field(default='CommandFileSetup', alias='@type')

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CommandFileReset(CommandFile):
    """A command file for resetting an experiment node."""

    id: str = Field(..., alias='@id')
    type: Literal['CommandFileReset'] = Field(default='CommandFileReset', alias='@type')
    bootedImage: Union["OSImage", EntityReference]  # Link to the booted image
    bootParameters: Optional[List[str]] = None  # List of boot parameters
    bootstrapCommands: Optional[List[Union["CommandFileBootstrap", EntityReference]]] = None  # Links to invoked bootstrap commands
    setupCommands: Optional[List[Union["CommandFileSetup", EntityReference]]] = None  # Links to invoked setup commands

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class OSImage(BaseModel):
    """An operating system image booted on an experiment node."""

    id: str = Field(..., alias='@id')
    type: Literal['OSImage'] = Field(default='OSImage', alias='@type')
    name: str  # Name of the image
    description: Optional[str] = None  # Description of the image
    fileSize: str  # Size of the image
    archivedAt: Optional[Union[EntityReference, str]] = None  # If the image is available online
    hasPart: Optional[List[Union["Dataset", "File", EntityReference]]] = None  # Links to image data if included in the crate

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class CommandFileCopy(CommandFile):
    """A command file for copying data to an experiment node."""

    id: str = Field(..., alias='@id')
    type: Literal['CommandFileCopy'] = Field(default='CommandFileCopy', alias='@type')
    sourcePath: str  # Source path of the data to be copied
    destinationPath: str  # Destination path of the data to be copied
    recursiveCopy: bool  # If the data is copied recursively
    copiedData: Optional[List[Union["Dataset", "File", EntityReference]]] = None  # Links to copied data if included in the crate

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class ExperimentNode(BaseModel):
    """An experiment node of a research infrastructure."""

    id: str = Field(..., alias='@id')
    type: Literal['ExperimentNode'] = Field(default='ExperimentNode', alias='@type')
    name: str  # Hostname of the experiment node
    description: Optional[str] = None  # Description of the experiment node
    hardware: Optional[Union["File", EntityReference]] = None  # Link to a hardware file of the experiment node
    topology: Optional[Union["File", EntityReference]] = None  # Link to a network topology file of the experiment node
    visualizedTopology: Optional[Union["File", EntityReference]] = None  # Link to a visualized network topology file of the experiment node

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class ProfileDefinition(BaseModel):
    """Entity describing the profile this crate conforms to."""

    id: str = Field(..., alias='@id')
    type: List[Literal['CreativeWork', 'Profile']] = Field(default=['CreativeWork', 'Profile'], alias='@type')
    name: str
    alternateName: Optional[str] = None
    version: str

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class RISEROCrateProfile(ProfileDefinition):
    """Prefilled profile definition for Research Infrastructure Shareable Experiments RO-Crate Profile v1.0.0"""
    id: Literal['https://tumi8.github.io/rise-ro-crate-profile/1.0.0/'] = Field(default='https://tumi8.github.io/rise-ro-crate-profile/1.0.0/', alias='@id')
    type: List[Literal['CreativeWork', 'Profile']] = Field(default=['CreativeWork', 'Profile'], alias='@type')
    name: Literal['Research Infrastructure Shareable Experiments RO-Crate Profile'] = Field(default='Research Infrastructure Shareable Experiments RO-Crate Profile')
    alternateName: Literal['RISE RO-Crate Profile'] = Field(default='RISE RO-Crate Profile')
    version: Literal['1.0.0'] = Field(default='1.0.0')

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class ROCrateGraph(BaseModel):
    """RO-Crate @graph container."""

    graph: List[Union[RootDataEntry, Experiment, File, Dataset, CommandFile, CommandFileLooped, LoopRun, CommandFileBootstrap, CommandFileSetup, CommandFileReset, OSImage, CommandFileCopy, ExperimentNode, Person, Organization, Role, CreativeWork, ScholarlyArticle, WebPage, LicenseApache20, LicenseCcBy40, LicenseCcBySa40, LicenseCc010, LicenseGpl30OrLater, LicenseMit, CreditRoleConceptualization, CreditRoleDataCuration, CreditRoleFormalAnalysis, CreditRoleFundingAcquisition, CreditRoleInvestigation, CreditRoleMethodology, CreditRoleProjectAdministration, CreditRoleResources, CreditRoleSoftware, CreditRoleSupervision, CreditRoleValidation, CreditRoleVisualization, CreditRoleWritingOriginalDraft, CreditRoleWritingReviewAndEditing, CustomJSONDataFormat, CustomPDF15Format, ProfileDefinition, EntityReference]] = Field(..., alias='@graph')

    model_config = ConfigDict(populate_by_name=True, extra='forbid')


class ROCrateMetadata(BaseModel):
    """Complete RO-Crate metadata file."""

    context: Union[str, List[Any], dict] = Field(..., alias='@context')
    graph: List[Union[RootDataEntry, Experiment, File, Dataset, CommandFile, CommandFileLooped, LoopRun, CommandFileBootstrap, CommandFileSetup, CommandFileReset, OSImage, CommandFileCopy, ExperimentNode, Person, Organization, Role, CreativeWork, ScholarlyArticle, WebPage, LicenseApache20, LicenseCcBy40, LicenseCcBySa40, LicenseCc010, LicenseGpl30OrLater, LicenseMit, CreditRoleConceptualization, CreditRoleDataCuration, CreditRoleFormalAnalysis, CreditRoleFundingAcquisition, CreditRoleInvestigation, CreditRoleMethodology, CreditRoleProjectAdministration, CreditRoleResources, CreditRoleSoftware, CreditRoleSupervision, CreditRoleValidation, CreditRoleVisualization, CreditRoleWritingOriginalDraft, CreditRoleWritingReviewAndEditing, CustomJSONDataFormat, CustomPDF15Format, ProfileDefinition, EntityReference]] = Field(..., alias='@graph')

    model_config = ConfigDict(populate_by_name=True, extra='forbid')
