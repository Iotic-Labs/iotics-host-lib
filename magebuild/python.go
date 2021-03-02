// +build mage

package main

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/Iotic-Labs/dev-mage-cli/bomb"
	"github.com/Iotic-Labs/dev-mage-cli/io"
	"github.com/Iotic-Labs/dev-mage-cli/python"
	"github.com/magefile/mage/mg"
	"github.com/magefile/mage/sh"
	comb "github.com/mxschmitt/golang-combinations"
)

var (
	virtualEnvironment = ".venv"
	py                 python.Python
)

type Python mg.Namespace

func (Python) init() {
	py = python.NewPython(virtualEnvironment)
}

func (Python) BuildAndPackage() {
	pyBuild := Python{}
	mg.SerialDeps(pyBuild.Env, pyBuild.Package)
}

func (Python) Env() {
	err := py.Setup("")
	bomb.IfError(err)
	err = py.RunInPyEnv("pip install -U pip setuptools")
	bomb.IfError(err)
	err = py.RunInPyEnv("pip install --no-cache-dir  -r python/requirements.txt")
	bomb.IfError(err)
}

func (Python) Package() {
	err := py.RunInPyEnv("./build_all.sh")
	bomb.IfError(err)
}

func (Python) Publish() {
	twine := python.NewTwine("./dist/*")
	twine.Publish()
}

func (Python) Clean() {
	sh.Run("rm", "-rf", "**/build")
	sh.Run("rm", "-rf", "build")
	sh.Run("rm", "-rf", "**/*.egg-info")
	sh.Run("rm", "-rf", "dist")
}

func (Python) CheckPackages() {
	for _, extension := range []string{".whl", ".tar.gz"} {
		combinations := comb.All([]string{"builder", "testing"})
		for _, combi := range combinations {
			runPkgInstallCheck(combi, extension)
		}
	}
}

func runPkgInstallCheck(combination []string, extension string) {
	dependencies := ""
	for _, c := range combination {
		dependencies = fmt.Sprintf("%s,%s", c, dependencies)
	}
	dependencies = strings.Trim(dependencies, ",")
	if len(dependencies) > 0 {
		dependencies = fmt.Sprintf("[%s]", dependencies)
	}
	pwd, _ := os.Getwd()
	pkg, err := filepath.Glob(fmt.Sprintf("%s/dist/iotics.host.lib-*%s", pwd, extension))
	bomb.IfError(err)
	if len(pkg) != 1 {
		bomb.Out(fmt.Sprintf("Setup error, exactly one meta package should be found in the dist directory: %+v", pkg))
	}
	pkg_name := filepath.Base(pkg[0])

	dockerBuildCmd := fmt.Sprintf("docker build -t checker --build-arg PIP_INDEX_URL=%s --build-arg PKG_NAME=%s "+
		"--build-arg DEPENDENCIES=%s  . -f Dockerfile.helper", os.Getenv("PIP_INDEX_URL"), pkg_name, dependencies)
	err = io.Run(dockerBuildCmd)
	bombIfDepError(err, dependencies, pkg_name)
	err = io.Run("docker run checker")
	bombIfDepError(err, dependencies, pkg_name)

}

func bombIfDepError(err error, dependencies string, pkg string) {
	if err != nil {
		fmt.Printf("Error checking pkg: '%s' install with dependencies:%s\n", pkg, dependencies)
		bomb.Err(err)
	}
}
