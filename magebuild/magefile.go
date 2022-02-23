// Copyright © 2021 to 2022 IOTIC LABS LTD. info@iotics.com
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://github.com/Iotic-Labs/iotics-host-lib/blob/master/LICENSE
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// +build mage

package main

import (
	"fmt"
	"os"
	"path"

	"github.com/magefile/mage/mg"
	"github.com/Iotic-Labs/dev-mage-cli/ci"
	"github.com/Iotic-Labs/dev-mage-cli/env"
	"github.com/Iotic-Labs/dev-mage-cli/gocd"

	// mage:import docker
	"github.com/Iotic-Labs/dev-mage-cli/docker"
)

type This mg.Namespace

var (
	pyBuild = Python{}
)

func init() {
	env.Default()
	fmt.Println("init")
	env.LoadUserEnvVars()
	homePath := os.Getenv("HOME")
	buildCaCert := env.GetEnv(env.BUILD_CA_CERT, true)
	// Python
	env.SetEnvVarIfNotSet("TWINE_CERT", path.Join(homePath, buildCaCert))
	env.SetEnvVarIfNotSet("TWINE_USERNAME", env.GetEnv(env.NEXUS_USERNAME, true))
	env.SetEnvVarIfNotSet("TWINE_PASSWORD", env.GetEnv(env.NEXUS_PASSWORD, true))
	env.SetEnvVarIfNotSet("PIP_USERNAME", env.GetEnv(env.NEXUS_USERNAME, true))
	env.SetEnvVarIfNotSet("PIP_PASSWORD", env.GetEnv(env.NEXUS_PASSWORD, true))
	env.SetEnvVarIfNotSet("PIP_CERT", path.Join(homePath, buildCaCert))

	// Docker
	env.SetEnvVarIfNotSet("DOCKER_BUILD_ARGS",
		fmt.Sprintf("PIP_INDEX_URL=%s", env.GetEnvValue(env.PIP_INDEX_URL)))

	version := os.Getenv(env.GO_PIPELINE_LABEL.String())
	// TODO Fix
	os.Setenv("VERSION", "dev")

	if gocd.IsAutomatedBuild() {
		docker.Init()
		docker.Login()
		fmt.Printf("automated build version: %s\n", version)
		os.Setenv("VERSION", version)
	}

	pyBuild.init()
}

// DockerBuild is a shortcut for a docker build (without tag or publish)
func (This) DockerBuild() {
	defer cleanupDocker()
	mg.SerialDeps(docker.KillAll, docker.Build)
}

// Login is a shortcut for a docker login
func (This) Login() {
	docker.Login()
}

// DockerPublish is a shortcut for a docker build with tag and publish
func (This) DockerPublish() {
	ci.DockerBuildAndPublish()
	if gocd.IsAutomatedBuild() {
		ci.GitTag()
	}
}
func cleanupDocker() {
	fmt.Println("removing temporary containers")
	docker.KillAll()
}
