#! /usr/bin/env python3

import logging
from typing import Optional, List
import httpx
import typer

from snyk_tags import __app_name__, __version__


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
)

app = typer.Typer()

# Reach to the API and generate tokens
def create_client(token: str) -> httpx.Client:
    return httpx.Client(
        base_url="https://snyk.io/api/v1", headers={"Authorization": f"token {token}"}
    )


def get_org_ids(token: str, group_id: str) -> list:
    """
    Get a list of org_ids based on the given group_id
    :param token:
    :param group_id:
    :return: list of org_ids
    """
    org_ids = []

    with create_client(token=token) as client:
        req = client.get(f"group/{group_id}/orgs")
        if req.status_code == 404:
            logging.error(
            f"Group id: {group_id} is invalid. Error message: {req.json()}."
        )
        orgs = client.get(f"group/{group_id}/orgs").json()
        
        for org in orgs.get("orgs"):
            org_ids.append(org["id"])
    return org_ids

# Apply tags
def apply_tag_to_project(
    client: httpx.Client, org_id: str, project_id: str, tag: str
) -> tuple:
    """
    Apply the Container tag to each given project

    :param client:
    :param org_id:
    :param project_id:
    :return: tuple of the status_code and dictionary of the JSON response
    """
    tag_data = {
        "key": "type",
        "value": tag,
    }
    req = client.post(f"org/{org_id}/project/{project_id}/tags", data=tag_data)

    if req.status_code == 200:
        logging.info(f"Successfully added {tag} tags to Project ID: {project_id}.")

    if req.status_code == 422:
        logging.warning(f"{tag} tag is already applied for Project ID: {project_id}.")

    if req.status_code == 404:
        logging.error(
            f"Project not found, likely a READ-ONLY project. Project ID: {project_id}. Error message: {req.json()}."
        )

    return req.status_code, req.json()


def apply_tags_to_projects(token: str, org_ids: list, type: str, tag: str) -> None:
    """
    Apply the tags to all Container projects within all orgs given in a list
    :param token:
    :param org_ids:
    :return: None
    """
    with create_client(token=token) as client:
        for org_id in org_ids:
            projects = client.post(f"org/{org_id}/projects").json()
            for project in projects.get("projects"):
                if project["type"] == type:
                    logging.debug(
                        apply_tag_to_project(
                            client=client, org_id=org_id, project_id=project["id"], tag=tag
                        )
                    )

# SAST Command
@app.command()
def sast(group_id: str = typer.Option(
            ..., 
            help="Group ID of the Snyk Group you want to apply the tags to",
            envvar=["GROUP_ID"]
        ), token: str = typer.Option(
            ...,
            help="SNYK API token",
            envvar=["SNYK_TOKEN"])
    ):

    logging.info(
        "This script will add the sast tag to every Snyk Code project in Snyk for easy filtering via the UI"
    )
    org_ids = get_org_ids(token, group_id)
    apply_tags_to_projects(token, org_ids, type='sast', tag='SAST')


# IaC Command
@app.command()
def iac(group_id: str = typer.Option(
            ..., 
            help="Group ID of the Snyk Group you want to apply the tags to",
            envvar=["GROUP_ID"]
        ), token: str = typer.Option(
            ...,
            help="SNYK API token",
            envvar=["SNYK_TOKEN"])
    ):

    logging.info(
        "This script will add the iac tag to every Snyk IaC project in Snyk for easy filtering via the UI"
    )
    org_ids = get_org_ids(token, group_id)
    apply_tags_to_projects(token, org_ids, type='iac', tag='IaC')

# SCA Command
@app.command()
def sca(group_id: str = typer.Option(
            ..., 
            help="Group ID of the Snyk Group you want to apply the tags to",
            envvar=["GROUP_ID"]
        ),  token: str = typer.Option(
            ...,
            help="SNYK API token",
            envvar=["SNYK_TOKEN"]
        ),  scaType: str = typer.Option(
            "maven", # Default value of comamand
            help="Type of package to update tags: maven, npm"
        )
    ):

    logging.info(
        "This script will add the SCA tag to every Snyk Open Source project in Snyk for easy filtering via the UI"
    )
    org_ids = get_org_ids(token, group_id)
    apply_tags_to_projects(token, org_ids, scaType, tag='SCA')

# Container Command
@app.command()
def container(group_id: str = typer.Option(
            ..., 
            help="Group ID of the Snyk Group you want to apply the tags to",
            envvar=["GROUP_ID"]
        ),  token: str = typer.Option(
            ...,
            help="SNYK API token",
            envvar=["SNYK_TOKEN"]
        ),  containerType: str = typer.Option(
            "deb", # Default value of comamand
            help="Type of container to update tags: Dockerfile, deb"
        )
    ):

    logging.info(
        "This script will add the container tag to every Snyk Container project in Snyk for easy filtering via the UI"
    )
    org_ids = get_org_ids(token, group_id)
    apply_tags_to_projects(token, org_ids, containerType, tag='Container')




