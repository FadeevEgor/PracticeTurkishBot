$DeploymentDirectory = "deployment"
$DependenciesZip = Join-Path -Path $DeploymentDirectory -ChildPath "dependencies_layer.zip"
$ConfigurationZip = Join-Path -Path $DeploymentDirectory -ChildPath "configuration_layer.zip"
$DeploymentZip = Join-Path -Path $DeploymentDirectory -ChildPath "deployment.zip"
if (Test-Path $DeploymentDirectory) {
    Remove-Item -Recurse -Force $DeploymentDirectory 
}
New-Item -Path "." -Name $DeploymentDirectory -ItemType "directory"

.\venv\Scripts\python.exe -m pip install -r .\requirements.txt --target .\python\ --use-pep517
zip -r $DependenciesZip .\python
Remove-Item -Recurse -Force .\python

zip $ConfigurationZip .\config.ini

zip $DeploymentZip .\database.py
zip $DeploymentZip .\lambda_function.py
zip $DeploymentZip .\service.py
zip $DeploymentZip .\telegram.py
zip $DeploymentZip .\word_of_the_day.py
