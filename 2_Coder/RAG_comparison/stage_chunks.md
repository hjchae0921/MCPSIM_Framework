# Documents retrieved at each coding stage

DOLFINx 0.10.0, Basix 0.10.0 and UFL 2025.2.1 supply the API references. The [source inventory](sources.json) records the official documentation revisions, the Python sources used for the shared index and their checksums.

Each procedure item retrieves three APIs by cosine similarity over the same 366 descriptions used for graph retrieval. Each link below opens the Markdown supplied for that API. Within a stage, repeated hits contribute their chunk only at the first occurrence.

From the repository root, `python main.py rag-context mesh` prints the mesh stage context. Add `--rankings` to print the scores. To regenerate the chunks from the bundled [official HTML](official_html), run `pip install -r 2_Coder/RAG_comparison/requirements.txt` followed by `python 2_Coder/RAG_comparison/chunk.py`.

## 1. Mesh

[Coding procedure](../agents/1_mesh/prompt.txt)

| Procedure item | First | Second | Third |
|---|---|---|---|
| 1 | [dolfinx.io.gmsh.read_from_msh](chunks/dolfinx.io.gmsh/dolfinx.io.gmsh.read_from_msh.md) | [dolfinx.io.gmsh.ufl_mesh](chunks/dolfinx.io.gmsh/dolfinx.io.gmsh.ufl_mesh.md) | [ufl.MeshView.ufl_mesh](chunks/ufl/ufl.MeshView.ufl_mesh.md) |
| 2 | [ufl.MeshView.ufl_mesh](chunks/ufl/ufl.MeshView.ufl_mesh.md) | [dolfinx.mesh.Geometry](chunks/dolfinx.mesh/dolfinx.mesh.Geometry.md) | [dolfinx.io.gmsh.MeshData](chunks/dolfinx.io.gmsh/dolfinx.io.gmsh.MeshData.md) |
| 3 | [dolfinx.mesh.MeshTags](chunks/dolfinx.mesh/dolfinx.mesh.MeshTags.md) | [dolfinx.io.gmsh.extract_topology_and_markers](chunks/dolfinx.io.gmsh/dolfinx.io.gmsh.extract_topology_and_markers.md) | [dolfinx.mesh.EntityMap](chunks/dolfinx.mesh/dolfinx.mesh.EntityMap.md) |
| 4 | [dolfinx.mesh.locate_entities](chunks/dolfinx.mesh/dolfinx.mesh.locate_entities.md) | [ufl.Measure](chunks/ufl/ufl.Measure.md) | [dolfinx.mesh.MeshTags](chunks/dolfinx.mesh/dolfinx.mesh.MeshTags.md) |

## 2. Function space

[Coding procedure](../agents/2_function_space/prompt.txt)

| Procedure item | First | Second | Third |
|---|---|---|---|
| 1 | [basix.ufl.mixed_element](chunks/basix.ufl/basix.ufl.mixed_element.md) | [basix.ufl.enriched_element](chunks/basix.ufl/basix.ufl.enriched_element.md) | [basix.ufl.element](chunks/basix.ufl/basix.ufl.element.md) |
| 2 | [dolfinx.fem.functionspace](chunks/dolfinx.fem/dolfinx.fem.functionspace.md) | [dolfinx.fem.create_vector](chunks/dolfinx.fem/dolfinx.fem.create_vector.md) | [dolfinx.fem.create_interpolation_data](chunks/dolfinx.fem/dolfinx.fem.create_interpolation_data.md) |
| 3 | [ufl.TrialFunctions](chunks/ufl/ufl.TrialFunctions.md) | [dolfinx.fem.functionspace](chunks/dolfinx.fem/dolfinx.fem.functionspace.md) | [dolfinx.fem.create_vector](chunks/dolfinx.fem/dolfinx.fem.create_vector.md) |

## 3. Weak form

[Coding procedure](../agents/3_weak_form/prompt.txt)

| Procedure item | First | Second | Third |
|---|---|---|---|
| 1 | [dolfinx.fem.Constant](chunks/dolfinx.fem/dolfinx.fem.Constant.md) | [dolfinx.fem.assemble_scalar](chunks/dolfinx.fem/dolfinx.fem.assemble_scalar.md) | [ufl.Form.constants](chunks/ufl/ufl.Form.constants.md) |
| 2 | [ufl.Form](chunks/ufl/ufl.Form.md) | [ufl.Measure](chunks/ufl/ufl.Measure.md) | [ufl.Measure.reconstruct](chunks/ufl/ufl.Measure.reconstruct.md) |

## 4. Boundary conditions

[Coding procedure](../agents/4_boundary_conditions/prompt.txt)

| Procedure item | First | Second | Third |
|---|---|---|---|
| 1 | [dolfinx.mesh.MeshTags](chunks/dolfinx.mesh/dolfinx.mesh.MeshTags.md) | [dolfinx.mesh.MeshTags.find](chunks/dolfinx.mesh/dolfinx.mesh.MeshTags.find.md) | [dolfinx.mesh.locate_entities](chunks/dolfinx.mesh/dolfinx.mesh.locate_entities.md) |
| 2 | [dolfinx.fem.FunctionSpace.sub](chunks/dolfinx.fem/dolfinx.fem.FunctionSpace.sub.md) | [dolfinx.fem.FunctionSpace.collapse](chunks/dolfinx.fem/dolfinx.fem.FunctionSpace.collapse.md) | [ufl.MixedFunctionSpace.ufl_sub_space](chunks/ufl/ufl.MixedFunctionSpace.ufl_sub_space.md) |
| 3 | [dolfinx.fem.locate_dofs_topological](chunks/dolfinx.fem/dolfinx.fem.locate_dofs_topological.md) | [dolfinx.fem.dirichletbc](chunks/dolfinx.fem/dolfinx.fem.dirichletbc.md) | [dolfinx.mesh.entities_to_geometry](chunks/dolfinx.mesh/dolfinx.mesh.entities_to_geometry.md) |

## 5. Solve

[Coding procedure](../agents/5_solve/prompt.txt)

| Procedure item | First | Second | Third |
|---|---|---|---|
| 1 | [dolfinx.fem.petsc.LinearProblem](chunks/dolfinx.fem.petsc/dolfinx.fem.petsc.LinearProblem.md) | [dolfinx.fem.petsc.NonlinearProblem](chunks/dolfinx.fem.petsc/dolfinx.fem.petsc.NonlinearProblem.md) | [dolfinx.fem.dirichletbc](chunks/dolfinx.fem/dolfinx.fem.dirichletbc.md) |
| 2 | [dolfinx.fem.petsc.NonlinearProblem](chunks/dolfinx.fem.petsc/dolfinx.fem.petsc.NonlinearProblem.md) | [dolfinx.fem.petsc.LinearProblem](chunks/dolfinx.fem.petsc/dolfinx.fem.petsc.LinearProblem.md) | [dolfinx.fem.petsc.assemble_residual](chunks/dolfinx.fem.petsc/dolfinx.fem.petsc.assemble_residual.md) |
| 3 | [dolfinx.fem.petsc.NonlinearProblem.solve](chunks/dolfinx.fem.petsc/dolfinx.fem.petsc.NonlinearProblem.solve.md) | [dolfinx.fem.petsc.LinearProblem.solve](chunks/dolfinx.fem.petsc/dolfinx.fem.petsc.LinearProblem.solve.md) | [dolfinx.fem.petsc.LinearProblem](chunks/dolfinx.fem.petsc/dolfinx.fem.petsc.LinearProblem.md) |

## 6. Postprocess

[Coding procedure](../agents/6_postprocess/prompt.txt)

| Procedure item | First | Second | Third |
|---|---|---|---|
| 1 | [dolfinx.fem.functionspace](chunks/dolfinx.fem/dolfinx.fem.functionspace.md) | [dolfinx.fem.Function.split](chunks/dolfinx.fem/dolfinx.fem.Function.split.md) | [dolfinx.fem.Function](chunks/dolfinx.fem/dolfinx.fem.Function.md) |
| 2 | [dolfinx.fem.FunctionSpace.tabulate_dof_coordinates](chunks/dolfinx.fem/dolfinx.fem.FunctionSpace.tabulate_dof_coordinates.md) | [dolfinx.fem.locate_dofs_geometrical](chunks/dolfinx.fem/dolfinx.fem.locate_dofs_geometrical.md) | [dolfinx.fem.Function.copy](chunks/dolfinx.fem/dolfinx.fem.Function.copy.md) |
| 3 | [ufl.Mesh.ufl_coordinate_element](chunks/ufl/ufl.Mesh.ufl_coordinate_element.md) | [dolfinx.fem.FunctionSpace.tabulate_dof_coordinates](chunks/dolfinx.fem/dolfinx.fem.FunctionSpace.tabulate_dof_coordinates.md) | [dolfinx.mesh.Topology.get_cell_permutation_info](chunks/dolfinx.mesh/dolfinx.mesh.Topology.get_cell_permutation_info.md) |
