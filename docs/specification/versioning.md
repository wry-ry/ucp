# Versioning

UCP uses string-based version identifiers following the format YYYY-MM-DD, to
indicate the last date backwards incompatible changes were made.

We will use long-lived release branches to manage specific versions of the spec
while keeping active development moving forward on main.

* When the Tech Council approves a new version of UCP, we will cut a
  new branch named release/YYYY-MM-DD directly from the current state of main.
    * We will implement a code freeze on the release branch the moment a
      release/YYYY-MM-DD branch is cut. Only critical bug fixes should move
      during this window, and they should be applied to the release branch
      first, then flowed back.
    * Critical fixes discovered during the release candidate phase should be
      applied based on the nature of the issue: they can either be implemented
      on the release branch first, then merged back into main to ensure the
      development line stays updated. Or, they could be developed on main and
      cherry-picked into the release branch to ensure both lines remain synced.
* Once finalized, we will merge the release branch into main and tag it (e.g
  git tag -a vYYYY-MM-DD).  We will use a GitHub Action to detect the new Tag
  and automatically generate a release notes draft and upload artifacts.
* Unlike temporary feature branches, release/YYYY-MM-DD branches are long-lived
  and correspond to specific versions of the spec for historical reference and
  maintenance.

## Breaking PRs

* Breaking changes should include `!` in the PR title
* Timing: We will announce the breaking change in Discussions 2 weeks
  before the change is merged.
