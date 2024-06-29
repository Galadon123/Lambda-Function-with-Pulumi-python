import pulumi
import pulumi_aws as aws

class ECRRepository:
    def __init__(self, name: str):
        self.repository = aws.ecr.Repository(name,
                                             image_scanning_configuration={"scanOnPush": True},
                                             tags={"Name": name})
        pulumi.export("ecr_repo_url", self.repository.repository_url)
        pulumi.export("ecr_registry", self.repository.registry_id)
